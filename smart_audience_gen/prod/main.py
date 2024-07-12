import streamlit as st
from src.ui_components import (
    render_company_input,
    render_company_description,
    render_json_output,
    render_actual_segments,
    render_audience_report,
    render_button
)

from src.api_clients import send_perplexity_message, send_groq_message, select_context
from src.audience_processing import process_audience_segments, summarize_segments
from src.data_processing import extract_and_correct_json
from src.report_generation import generate_audience_report
from config.prompts import (
    COMPANY_RESEARCH_PROMPT,
    AUDIENCE_BUILD_PROMPT,
    JSON_AUDIENCE_BUILD_PROMPT,
    INCLUDED_IMPROVING_PROMPT,
    EXCLUDED_IMPROVING_PROMPT,
    REPHRASAL_PROMPT
)
from config.settings import PINECONE_TOP_K

def process_message_queue(message_queue, initial_history=None):
    history = initial_history or []
    results = {}
    
    for step, (prompt_name, prompt, format_args) in enumerate(message_queue, 1):
        st.text(f"Step {step}/{len(message_queue)}: {prompt_name}")
        formatted_prompt = prompt.format(**format_args) if format_args else prompt
        response, history = send_groq_message(formatted_prompt, select_context(history, num_first=2, num_recent=7))
        results[prompt_name] = response
    
    return results, history

def generate_company_description(company_name):
    return send_perplexity_message(COMPANY_RESEARCH_PROMPT.format(company_name=company_name), [])

def generate_audience(company_name, company_description):
    message_queue = [
        ("Planning audience", AUDIENCE_BUILD_PROMPT, {"company_name": company_name, "company_description": company_description}),
        ("Structuring audience as JSON", JSON_AUDIENCE_BUILD_PROMPT, None),
        ("Improving included segments", INCLUDED_IMPROVING_PROMPT, None),
        ("Improving excluded segments", EXCLUDED_IMPROVING_PROMPT, None),
        ("Rephrasing segments", REPHRASAL_PROMPT, {"company_name": company_name})
    ]

    results, _ = process_message_queue(message_queue)
    last_key = list(results.keys())[-1]
    return extract_and_correct_json(results[last_key])

def process_audience_data(extracted_json):
    processed_results = process_audience_segments(extracted_json, presearch_filter={}, top_k=PINECONE_TOP_K)
    summary_results = summarize_segments(processed_results)
    return summary_results

def main():
    st.set_page_config(layout="wide")
    st.title("Smart Audience Generator")

    company_name = render_company_input()

    if 'stage' not in st.session_state:
        st.session_state.stage = 0

    if st.session_state.stage == 0:
        if render_button("Generate Company Description"):
            st.session_state.company_description = generate_company_description(company_name)
            st.session_state.stage = 1

    if st.session_state.stage >= 1:
        edited_company_description = render_company_description(st.session_state.company_description)
        if render_button("Generate Audience"):
            st.session_state.edited_company_description = edited_company_description
            st.session_state.stage = 2
            st.session_state.pop('extracted_json', None)
            st.session_state.pop('processed_results', None)
            st.session_state.pop('summary_results', None)
            st.session_state.pop('audience_report', None)

    if st.session_state.stage >= 2:
        if 'extracted_json' not in st.session_state:
            with st.spinner("Generating audience..."):
                extracted_json = generate_audience(company_name, st.session_state.edited_company_description)
                if extracted_json:
                    st.session_state.extracted_json = extracted_json
                else:
                    st.error("Failed to extract valid JSON")
                    return

        render_json_output(st.session_state.extracted_json)
        
        if render_button("Search Actual Segments"):
            st.session_state.pop('processed_results', None)
            st.session_state.pop('summary_results', None)
            st.session_state.pop('audience_report', None)
            st.session_state.stage = 3
            st.rerun()

    if st.session_state.stage >= 3:
        with st.spinner("Processing audience segments..."):
            if 'summary_results' not in st.session_state:
                st.session_state.summary_results = process_audience_data(st.session_state.extracted_json)
        
        render_actual_segments(st.session_state.summary_results)
        
        if 'audience_report' not in st.session_state:
            with st.spinner("Generating audience report..."):
                st.session_state.audience_report = generate_audience_report(st.session_state.summary_results, company_name)
        
        render_audience_report(st.session_state.audience_report)

if __name__ == "__main__":
    main()