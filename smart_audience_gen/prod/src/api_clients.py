import os
from typing import List, Tuple
from config import ONLINE_MODEL, PPLX_API_KEY, OPENAI_API_KEY, GROQ_API_KEY, OPENAI_MODEL, GROQ_MODEL, BASIC_SYSTEM_PROMPT
import requests
from openai import OpenAI
from groq import Groq
from tenacity import retry, stop_after_attempt, wait_exponential


openai_client = OpenAI(api_key=OPENAI_API_KEY)
groq_client = Groq(api_key=GROQ_API_KEY)

def send_perplexity_message(message, conversation_history, model=ONLINE_MODEL, system_prompt=BASIC_SYSTEM_PROMPT):
    url = "https://api.perplexity.ai/chat/completions"
    
    conversation_history.append({"role": "user", "content": message})
    
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt}
        ] + conversation_history
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PPLX_API_KEY}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if 'choices' in response_data and len(response_data['choices']) > 0:
        ai_response = response_data['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response
    else:
        return "Error: Unable to get a response from the API"

def select_context(history, num_first, num_recent):
    if len(history) <= num_first + num_recent:
        return history
    print('history length' + str(len(history)))
    return history[:num_first] + history[-(num_recent):]

def prepare_messages(message, conversation_history, system_prompt):
    messages = conversation_history.copy()
    
    if system_prompt and (not messages or messages[0]["role"] != "system"):
        messages.insert(0, {"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": message})
    return messages

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def send_api_message(client, message, conversation_history, model, system_prompt):
    messages = prepare_messages(message, conversation_history, system_prompt)
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.0
        )
        ai_response = response.choices[0].message.content
        messages.append({"role": "assistant", "content": ai_response})
        return ai_response, messages
    except Exception as e:
        error_message = f"Error: Unable to get a response from the API. {str(e)}"
        return error_message, messages

def send_openai_message(message, conversation_history, model=OPENAI_MODEL, system_prompt=BASIC_SYSTEM_PROMPT):
    return send_api_message(openai_client, message, conversation_history, model, system_prompt)

def send_groq_message(message, conversation_history, model=GROQ_MODEL, system_prompt=BASIC_SYSTEM_PROMPT):
    return send_api_message(groq_client, message, conversation_history, model, system_prompt)