import requests
from openai import OpenAI
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
from config.settings import ONLINE_MODEL, PPLX_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, OPEN_ROUTER_KEY, OPENAI_MODEL, OPEN_ROUTER_MODEL, GROQ_MODEL, CONTEXT_LENGTH_START, CONTEXT_LENGTH_END, API_SELECTOR
from config.prompts import BASIC_SYSTEM_PROMPT
import logging

logger = logging.getLogger(__name__)


openai_client = OpenAI(api_key=OPENAI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)
open_router_client = client = OpenAI(
  base_url="https://openrouter.ai/api/v1",
  api_key=OPEN_ROUTER_KEY,
)

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=30, max=200),
    before_sleep=before_sleep_log(logger, logging.INFO)
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
        raise Exception("Error: Unable to get a response from the API")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=2, min=10, max=60),
    before_sleep=before_sleep_log(logger, logging.INFO)
)
def send_api_message(client, messages, model):
    response = client.chat.completions.create(
        model=model,
        messages=select_context(messages, CONTEXT_LENGTH_START, CONTEXT_LENGTH_END),
        temperature=0.0,
        timeout=30
    )
    logger.info(f"API call {response}")
    
    if response.choices and len(response.choices) > 0:
        return response.choices[0].message.content
    else:
        raise Exception("Error: Unable to get a response from the API")
    
def select_context(history, num_first, num_recent):
    if len(history) <= num_first + num_recent:
        return history
    print('history length' + str(len(history)))
    return history[:num_first] + history[-(num_recent):]

def route_api_call(api_selector = API_SELECTOR, messages = []):
    if api_selector == 'openai':
        return send_api_message(openai_client, messages, OPENAI_MODEL)
    elif api_selector == 'groq':
        return send_api_message(groq_client, messages, GROQ_MODEL)
    elif api_selector == 'open_router':
        return send_api_message(open_router_client, messages, OPEN_ROUTER_MODEL)