import requests
from openai import OpenAI
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential
from config.settings import ONLINE_MODEL, PPLX_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, OPENAI_MODEL, GROQ_MODEL, CONTEXT_LENGTH_START, CONTEXT_LENGTH_END, API_SELECTOR
from config.prompts import BASIC_SYSTEM_PROMPT



openai_client = OpenAI(api_key=OPENAI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

if API_SELECTOR == 'openai':
    client = openai_client
    model = OPENAI_MODEL
elif API_SELECTOR == 'groq':
    client = groq_client
    model = GROQ_MODEL

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

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def send_api_message(client, messages, model):
    try:
        response = client.chat.completions.create(
            model=model,
            messages=select_context(messages, CONTEXT_LENGTH_START, CONTEXT_LENGTH_END),
            temperature=0.0
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: Unable to get a response from the API. {str(e)}"
    
def select_context(history, num_first, num_recent):
    if len(history) <= num_first + num_recent:
        return history
    print('history length' + str(len(history)))
    return history[:num_first] + history[-(num_recent):]

def route_api_call(messages, model=model):
    return send_api_message(client, messages, model)