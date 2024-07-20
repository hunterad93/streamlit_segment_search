from src.api_clients import route_api_call
from config.prompts import REPORT_PROMPT, REPORT_SYSTEM_PROMPT
import streamlit as st

def generate_audience_report(summary_json, company_name, conversation_history):

    # Prepare the report prompt
    formatted_report_prompt = REPORT_PROMPT.format(
        summary_json=summary_json,
        company_name=company_name
    )

    # Add the system prompt and the report prompt to the conversation history
    conversation_history.append({"role": "system", "content": REPORT_SYSTEM_PROMPT})
    conversation_history.append({"role": "user", "content": formatted_report_prompt})

    # Send the message to the LLM
    audience_report = route_api_call('openai', conversation_history)

    # Add the LLM's response to the conversation history
    conversation_history.append({"role": "assistant", "content": audience_report})

    return audience_report, conversation_history