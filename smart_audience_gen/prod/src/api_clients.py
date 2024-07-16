import requests
from openai import OpenAI
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception, before_sleep
from config.settings import ONLINE_MODEL, PPLX_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, OPENAI_MODEL, GROQ_MODEL, CONTEXT_LENGTH_START, CONTEXT_LENGTH_END, API_SELECTOR
from config.prompts import BASIC_SYSTEM_PROMPT
import logging
import streamlit as st

logger = logging.getLogger(__name__)


openai_client = OpenAI(api_key=OPENAI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

if API_SELECTOR == 'openai':
    client = openai_client
    model = OPENAI_MODEL
elif API_SELECTOR == 'groq':
    client = groq_client
    model = GROQ_MODEL

def is_rate_limit_error(exception):
    return isinstance(exception, requests.exceptions.HTTPError) and exception.response.status_code == 429

def show_retry_warning(retry_state):
    exception = retry_state.outcome.exception()
    if is_rate_limit_error(exception):
        message = (f"Rate limit hit. Retrying in {retry_state.next_action.sleep:.2f} seconds. "
                   f"Attempt {retry_state.attempt_number} of {retry_state.stop.max_attempt_number}")
        st.warning(message)

def before_sleep_show_warning(retry_state):
    show_retry_warning(retry_state)


@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=10, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    before_sleep=before_sleep_show_warning
)
def send_perplexity_message(messages, model=ONLINE_MODEL):
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": model,
        "messages": messages
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PPLX_API_KEY}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if 'choices' in response_data and len(response_data['choices']) > 0:
        return response_data['choices'][0]['message']['content']
    else:
        return "Error: Unable to get a response from the API"

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=10, max=60),
    retry=retry_if_exception(is_rate_limit_error),
    before_sleep=before_sleep_show_warning
)
def send_api_message(client, messages, model):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=select_context(messages, CONTEXT_LENGTH_START, CONTEXT_LENGTH_END),
            temperature=0.0
        )
        return response.choices[0].message.content
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 429:
            st.warning(f"Rate limit error occurred: {str(e)}")
            raise  # Re-raise the exception to trigger the retry
        else:
            error_message = f"HTTP error occurred: {str(e)}"
            st.error(error_message)
            return error_message
    except Exception as e:
        error_message = f"Error: Unable to get a response from the API. {str(e)}"
        st.error(error_message)
        return error_message
    
def select_context(history, num_first, num_recent):
    if len(history) <= num_first + num_recent:
        return history
    print('history length' + str(len(history)))
    return history[:num_first] + history[-(num_recent):]

def route_api_call(messages, model=model):
    return send_api_message(client, messages, model)