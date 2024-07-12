from src.api_clients import send_perplexity_message, send_groq_message
from src.data_processing import extract_and_correct_json
from config.prompts import (
    COMPANY_RESEARCH_PROMPT,
    AUDIENCE_BUILD_PROMPT,
    JSON_AUDIENCE_BUILD_PROMPT,
    INCLUDED_IMPROVING_PROMPT,
    EXCLUDED_IMPROVING_PROMPT,
    REPHRASAL_PROMPT
)

def process_message_queue(message_queue, conversation_history):
    results = {}
    
    for step, (prompt_name, prompt, format_args) in enumerate(message_queue, 1):
        formatted_prompt = prompt.format(**format_args) if format_args else prompt
        conversation_history.append({"role": "user", "content": formatted_prompt})
        
        response = send_groq_message(conversation_history)
        conversation_history.append({"role": "assistant", "content": response})
        
        results[prompt_name] = response
    
    return results, conversation_history

def generate_company_description(company_name, conversation_history):
    prompt = COMPANY_RESEARCH_PROMPT.format(company_name=company_name)
    conversation_history.append({"role": "user", "content": prompt})
    
    response = send_perplexity_message(conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    
    return response, conversation_history

def generate_audience_segments(company_name, company_description, conversation_history):
    message_queue = [
        ("Planning audience", AUDIENCE_BUILD_PROMPT, {"company_name": company_name, "company_description": company_description}),
        ("Structuring audience as JSON", JSON_AUDIENCE_BUILD_PROMPT, None),
        ("Improving included segments", INCLUDED_IMPROVING_PROMPT, None),
        ("Improving excluded segments", EXCLUDED_IMPROVING_PROMPT, None),
        ("Rephrasing segments", REPHRASAL_PROMPT, {"company_name": company_name})
    ]

    results, updated_history = process_message_queue(message_queue[:2], conversation_history)
    last_key = list(results.keys())[-1]
    return extract_and_correct_json(results[last_key]), updated_history

def generate_audience(company_name, conversation_history):
    """Main function to generate audience"""
    company_description, updated_history = generate_company_description(company_name, conversation_history)
    audience_segments, final_history = generate_audience_segments(company_name, company_description, updated_history)
    return audience_segments, final_history