from config import ONLINE_SYSTEM_PROMPT, OFFLINE_SYSTEM_PROMPT, SUMMARY_PROMPT, ONLINE_MODEL, OFFLINE_MODEL, BASIC_SYSTEM_PROMPT, INITIAL_RESEARCH_PROMPT, FOLLOW_UP_PROMPT, CATEGORIZE_SEGMENT_PROMPT
from src.api_clients import send_perplexity_message

def categorize_segment(segment):
    messages = [{"role": "user", "content": CATEGORIZE_SEGMENT_PROMPT.format(segment=segment)}]
    response = send_perplexity_message(messages, ONLINE_MODEL, ONLINE_SYSTEM_PROMPT)
    return response

def summarize_conversation(initial_prompt, conversation_history):
    formatted_summary_prompt = SUMMARY_PROMPT.format(
        initial_prompt=initial_prompt,
        conversation_history=conversation_history
    )
    summary = send_perplexity_message(
        [{"role": "user", "content": formatted_summary_prompt}],
        OFFLINE_MODEL,
        BASIC_SYSTEM_PROMPT
    )
    return summary

def create_conversation(domain, segment, num_iterations):
    online_model = ONLINE_MODEL
    offline_model = OFFLINE_MODEL
    
    online_conversation = []
    offline_conversation = []
    
    # Replace 'Data Alliance' with 'The Trade Desk Data Alliance'
    if domain == "Data Alliance":
        domain = "The Trade Desk Data Alliance"

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
        online_response = send_perplexity_message(online_conversation, online_model, ONLINE_SYSTEM_PROMPT)
        online_conversation.append({"role": "assistant", "content": online_response})
        
        # Update offline conversation
        offline_conversation = online_conversation.copy()
        
        if i < num_iterations - 1:
            # Generate follow-up question using offline model
            offline_conversation.append({"role": "user", "content": FOLLOW_UP_PROMPT})
            follow_up_question = send_perplexity_message(offline_conversation, offline_model, OFFLINE_SYSTEM_PROMPT)
            
            # Add follow-up question to conversations
            online_conversation.append({"role": "user", "content": follow_up_question})

    summary = summarize_conversation(initial_prompt, offline_conversation)
    
    return offline_conversation, summary