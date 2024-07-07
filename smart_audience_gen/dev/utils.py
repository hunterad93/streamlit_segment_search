import requests
from dotenv import load_dotenv
import os
from openai import OpenAI
from groq import Groq

load_dotenv('/Users/adamhunter/miniconda3/envs/ragdev/ragdev.env')
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

def send_perplexity_message(message, conversation_history, model="llama-3-sonar-large-32k-online", system_prompt="Be concise and precise."):
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
        "authorization": f"Bearer {os.getenv('PPLX_API_KEY')}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if 'choices' in response_data and len(response_data['choices']) > 0:
        ai_response = response_data['choices'][0]['message']['content']
        conversation_history.append({"role": "assistant", "content": ai_response})
        return ai_response
    else:
        return "Error: Unable to get a response from the API"

def send_openai_message(message, conversation_history, model="gpt-4o", system_prompt=None):
    messages = conversation_history.copy()
    
    if system_prompt and (not messages or messages[0]["role"] != "system"):
        messages.insert(0, {"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": message})
    
    try:
        response = openai_client.chat.completions.create(
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
    
def send_groq_message(message, conversation_history, model="llama3-70b-8192", system_prompt=None):
    messages = conversation_history.copy()
    
    if system_prompt and (not messages or messages[0]["role"] != "system"):
        messages.insert(0, {"role": "system", "content": system_prompt})
    
    messages.append({"role": "user", "content": message})
    
    try:
        response = groq_client.chat.completions.create(
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