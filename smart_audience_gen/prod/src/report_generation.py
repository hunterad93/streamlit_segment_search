import json
from typing import Dict
from src.api_clients import send_groq_message
from config.prompts import REPORT_PROMPT, REPORT_SYSTEM_PROMPT

def generate_audience_report(summary_json, company_name):
    formatted_report_prompt = REPORT_PROMPT.format(
        summary_json=summary_json,
        company_name=company_name
    )
    audience_report = send_groq_message(formatted_report_prompt, [], system_prompt=REPORT_SYSTEM_PROMPT)

    return audience_report