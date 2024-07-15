from config.settings import ONLINE_MODEL, OFFLINE_MODEL
from config.prompts import ONLINE_SYSTEM_PROMPT, OFFLINE_SYSTEM_PROMPT, SUMMARY_PROMPT, INITIAL_RESEARCH_PROMPT, FOLLOW_UP_PROMPT, CATEGORIZE_SEGMENT_PROMPT, BASIC_SYSTEM_PROMPT
from src.api_clients import send_perplexity_message

def categorize_segment(segment):
    messages = [{"role": "user", "content": CATEGORIZE_SEGMENT_PROMPT.format(segment=segment)}]
    response = send_perplexity_message(messages, OFFLINE_MODEL)
    return response

def summarize_conversation(initial_prompt, conversation_history):
    formatted_summary_prompt = SUMMARY_PROMPT.format(
        initial_prompt=initial_prompt,
        conversation_history=conversation_history
    )
    summary = send_perplexity_message(
        [{"role": "user", "content": formatted_summary_prompt}],
        OFFLINE_MODEL
    )
    return summary

def create_conversation(domain, segment, num_iterations):
    online_model = ONLINE_MODEL
    offline_model = OFFLINE_MODEL
    
    online_conversation = []
    offline_conversation = []
    
    # Replace 'Data Alliance' with 'The Trade Desk Data Alliance'
    if domain == "Data Alliance":
        summary = "The Trade Desk Data Alliance curates the highest quality 3rd party data available for purchase. We trust their curation and prefer using their segments whenever they are available."
        return [], summary
    
    data_type = categorize_segment(segment)

    # Initial query
    initial_prompt = INITIAL_RESEARCH_PROMPT.format(
        domain=domain,
        data_type=data_type
    )

    online_conversation.append({"role": "user", "content": initial_prompt})
    print(initial_prompt)
    for i in range(num_iterations):
        # Get response from online model
        online_response = send_perplexity_message(online_conversation, online_model)
        online_conversation.append({"role": "assistant", "content": online_response})
        
        # Update offline conversation
        offline_conversation = online_conversation.copy()
        
        if i < num_iterations - 1:
            # Generate follow-up question using offline model
            offline_conversation.append({"role": "user", "content": FOLLOW_UP_PROMPT})
            follow_up_question = send_perplexity_message(offline_conversation, offline_model)
            
            # Add follow-up question to conversations
            online_conversation.append({"role": "user", "content": follow_up_question})

    summary = summarize_conversation(initial_prompt, offline_conversation)
    
    return offline_conversation, summary

def generate_segment_summaries(segments):
    summaries = []
    for segment in segments:
        conversation, summary = create_conversation(segment['BrandName'], segment['raw_string'], num_iterations=3)
        summaries.append({
            "raw_string": segment['raw_string'],
            "brand_name": segment['BrandName'],
            "summary": summary
        })
    return summaries

def generate_methodology_summary(segment_summaries):
    combined_summaries = "\n\n".join([f"Segment: {s['raw_string']}\nBrand: {s['brand_name']}\nSummary: {s['summary']}" for s in segment_summaries])
    
    return combined_summaries
