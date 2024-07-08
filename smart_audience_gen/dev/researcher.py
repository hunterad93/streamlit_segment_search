import requests
from config import PPLX_API_KEY

# Constants for system prompts
ONLINE_SYSTEM_PROMPT = """Act as an advocate for the company you are asked about. Conclude your response with a list of URLS used from your search."""

OFFLINE_SYSTEM_PROMPT = """You are an AI assistant who is trying to get specific information about data brokers 
from a conversation partner who is connected to the internet. Your **ONLY** concern is the accuracy of the data, because 
you are investigating on behalf of advertisers who are paying for the data."""

SUMMARY_PROMPT = "Be precise and concise. Only provide the summary, without restating the question, or giving additional context or explanation. Make the summary sound like a natural, human explanation rather than a marketing spiel."    

def send_perplexity_message(conversation_history, model, system_prompt):
    url = "https://api.perplexity.ai/chat/completions"
    
    messages = [{"role": "system", "content": system_prompt}] + conversation_history
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {PPLX_API_KEY}"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    response_data = response.json()
    
    if 'choices' in response_data and len(response_data['choices']) > 0:
        input_tokens = response_data.get('usage', {}).get('prompt_tokens', 0)
        output_tokens = response_data.get('usage', {}).get('completion_tokens', 0)
        print(f"Input tokens: {input_tokens}, Output tokens: {output_tokens}")
        return response_data['choices'][0]['message']['content']
    else:
        print(response_data)
        return "Error: Unable to get a response from the LLM"
    

def categorize_segment(segment):
    messages = [{"role": "user", "content": f"""In short phrase categorize this data marketplace offering {segment}. Please provide only the brief categorization without any addditional explanation. Example categorizations would include: behavioral, demographic, financial, purchase behavior, value based, needs based etc."""}]
    response = send_perplexity_message(messages, "llama-3-sonar-large-32k-chat", "You are an digital marketing expert who responds with only one or two words.")
    print(response)
    return response

def summarize_conversation(initial_prompt, conversation_history):
    summary_prompt = f"""Based on the following conversation about '{initial_prompt}', provide a concise summary for a non-technical advertiser. 
    Focus on answering the initial question and find a single answer to satisfy the question. Keep it brief and easy to understand.

    Conversation:
    {conversation_history}

    Summary:"""
    
    summary = send_perplexity_message([{"role": "user", "content": summary_prompt}], "llama-3-sonar-large-32k-chat", SUMMARY_PROMPT)
    return summary

def create_conversation(domain, segment, num_iterations):
    online_model = "llama-3-sonar-large-32k-online"
    offline_model = "llama-3-sonar-large-32k-chat"
    
    online_conversation = []
    offline_conversation = []
    
    # Replace 'Data Alliance' with 'The Trade Desk Data Alliance'
    if domain == "Data Alliance":
        domain = "The Trade Desk Data Alliance"

    data_type = categorize_segment(segment)

    # Initial query
    initial_prompt = f"Answer this question: how does {domain} collect {data_type} data that it sells to advertisers?"

    online_conversation.append({"role": "user", "content": initial_prompt})
    print(initial_prompt)
    for i in range(num_iterations):
        # Get response from online model
        online_response = send_perplexity_message(online_conversation, online_model, ONLINE_SYSTEM_PROMPT)
        online_conversation.append({"role": "assistant", "content": online_response})
        
        # Update offline conversation
        offline_conversation = online_conversation.copy()
        
        if i < num_iterations - 1:
            # Generate follow-up question using offline model
            follow_up_prompt = "Based on the previous conversation, generate a follow-up question to get more specific information. Phrase it as if you're the original user seeking clarification. Only provide the question, without any additional context or explanation."
            offline_conversation.append({"role": "user", "content": follow_up_prompt})
            follow_up_question = send_perplexity_message(offline_conversation, offline_model, OFFLINE_SYSTEM_PROMPT)
            
            # Add follow-up question to conversations
            online_conversation.append({"role": "user", "content": follow_up_question})

    summary = summarize_conversation(initial_prompt, offline_conversation)
    
    return offline_conversation, summary


