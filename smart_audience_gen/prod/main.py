import streamlit as st
import json

from src.api_clients import send_perplexity_message, send_groq_message, send_openai_message, select_context
from src.audience_processing import process_audience_segments, summarize_segments
from src.data_processing import extract_and_correct_json
from src.report_generation import generate_audience_report
from config import AUDIENCE_BUILD_PROMPT, JSON_AUDIENCE_BUILD_PROMPT, INCLUDED_IMPROVING_PROMPT, EXCLUDED_IMPROVING_PROMPT, COMPANY_RESEARCH_PROMPT, PINECONE_TOP_K, REPHRASAL_PROMPT, AND_OR_PROMPT

def main():
    st.set_page_config(layout="wide")
    st.title("Smart Audience Generator")

    company_name = st.text_input("Enter company name:", "Bubba Burgers")

    if 'stage' not in st.session_state:
        st.session_state.stage = 0

    if st.session_state.stage == 0 and st.button("Generate Company Description"):
        company_description = send_perplexity_message(COMPANY_RESEARCH_PROMPT.format(company_name=company_name), [])
        st.session_state.company_description = company_description
        st.session_state.stage = 1

    if st.session_state.stage >= 1:
        edited_company_description = st.text_area("Edit company description:", st.session_state.company_description, height=300)
        if st.button("Generate Audience"):
            st.session_state.edited_company_description = edited_company_description
            st.session_state.stage = 2
            # Clear previous results when regenerating
            st.session_state.pop('extracted_json', None)
            st.session_state.pop('processed_results', None)
            st.session_state.pop('summary_results', None)
            st.session_state.pop('audience_report', None)

    if st.session_state.stage >= 2:
        if 'extracted_json' not in st.session_state:
            with st.spinner("Generating audience..."):
                st.text("Step 1/5: Planning audience")
                ai_response, updated_history = send_groq_message(AUDIENCE_BUILD_PROMPT.format(company_name=company_name, company_description=st.session_state.edited_company_description), [])
                
                st.text("Step 2/5: Structuring audience as JSON")
                json_audience_build_response, updated_history = send_groq_message(JSON_AUDIENCE_BUILD_PROMPT, select_context(updated_history, num_first=2, num_recent=7))
                
                st.text("Step 3/5: Improving included segments")
                improving_included_response, updated_history = send_groq_message(INCLUDED_IMPROVING_PROMPT, select_context(updated_history, num_first=2, num_recent=7))
                
                st.text("Step 4/5: Improving excluded segments")
                improving_excluded_response, updated_history = send_groq_message(EXCLUDED_IMPROVING_PROMPT, select_context(updated_history, num_first=2, num_recent=7))
                
                st.text("Step 5/5: Rephrasing segments, adding operators")
                rephrased_response, updated_history = send_groq_message(REPHRASAL_PROMPT, select_context(updated_history, num_first=2, num_recent=7))


                extracted_json = extract_and_correct_json(rephrased_response)
                if extracted_json:
                    st.session_state.extracted_json = extracted_json
                else:
                    st.error("Failed to extract valid JSON")
                    return

        st.subheader("Generated Hypothetical Audience Segments")
        st.json(st.session_state.extracted_json)
        st.json(st.session_state.extracted_operator_json)
        
        if st.button("Search Actual Segments"):
            # Clear previous results when searching again
            st.session_state.pop('processed_results', None)
            st.session_state.pop('summary_results', None)
            st.session_state.pop('audience_report', None)
            st.session_state.stage = 3
            st.rerun()  # Force a rerun to update the UI

    if st.session_state.stage >= 3:
        with st.spinner("Processing audience segments..."):
            if 'processed_results' not in st.session_state:
                processed_results = process_audience_segments(st.session_state.extracted_json, top_k=PINECONE_TOP_K)
                st.session_state.processed_results = processed_results
            
            if 'summary_results' not in st.session_state:
                summary_results = summarize_segments(st.session_state.processed_results)
                st.session_state.summary_results = summary_results
        
        st.subheader("Actual Segments")
        st.json(st.session_state.summary_results)
        
        if 'audience_report' not in st.session_state:
            with st.spinner("Generating audience report..."):
                audience_report = generate_audience_report(st.session_state.summary_results, company_name)
                st.session_state.audience_report = audience_report
        
        st.subheader("Audience Report")
        st.markdown(st.session_state.audience_report[0])

if __name__ == "__main__":
    main()