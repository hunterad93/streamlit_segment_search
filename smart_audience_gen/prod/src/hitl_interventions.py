import streamlit as st
from src.api_clients import route_api_call

def refine_artifact(
    artifact_name,
    chat_container,
    system_prompt,
    conversation_history=None,
    done_keyword="done"
):
    # Display existing conversation (excluding system message)
    for message in conversation_history[1:]:
        chat_container.chat_message(message["role"]).write(message["content"])

    user_input = st.chat_input(f"Your feedback (type '{done_keyword}' when finished):", key=f"chat_input_{artifact_name}_refine")
    
    if user_input:
        if user_input.lower() == done_keyword:
            return conversation_history[-1]["content"], conversation_history
        
        refined_artifact, updated_history = route_api_call(user_input, conversation_history, system_prompt=system_prompt)
        
        chat_container.chat_message("user").write(user_input)
        chat_container.chat_message("assistant").write(refined_artifact)
        
        return refined_artifact, updated_history

    return None, conversation_history