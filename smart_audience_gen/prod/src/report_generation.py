from src.api_clients import route_api_call
from config.prompts import REPORT_PROMPT, REPORT_SYSTEM_PROMPT
import streamlit as st
import copy

def generate_audience_report(summary_json, company_name, conversation_history):
    # Create a local copy of the conversation history
    local_history = copy.deepcopy(conversation_history)

    # Prepare the report prompt
    formatted_report_prompt = REPORT_PROMPT.format(
        summary_json=summary_json,
        company_name=company_name
    )

    # Add the system prompt and the report prompt to the local conversation history
    local_history.append({"role": "system", "content": REPORT_SYSTEM_PROMPT})
    local_history.append({"role": "user", "content": formatted_report_prompt})

    # Send the message to the LLM using the local history
    audience_report = route_api_call('openai', local_history)

    return audience_report