import streamlit as st
import json
import concurrent.futures

from src.api_clients import send_perplexity_message, send_groq_message, send_openai_message, select_context
from src.audience_processing import process_audience_segments, summarize_segments, hypothetical_audience_gen
from src.segment_processing import rate_broadness_single_segment
from src.data_processing import extract_and_correct_json, extract_segment_descriptions, add_broadness_scores_to_json
from src.report_generation import generate_audience_report
from config import AUDIENCE_BUILD_PROMPT, JSON_AUDIENCE_BUILD_PROMPT, INCLUDED_IMPROVING_PROMPT, EXCLUDED_IMPROVING_PROMPT, COMPANY_RESEARCH_PROMPT, PINECONE_TOP_K, REPHRASAL_PROMPT, AND_OR_PROMPT, DEMOGRAPHIC_AUDIENCE_BUILD_PROMPT, BEHAVIORAL_AUDIENCE_BUILD_PROMPT

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
                with st.spinner("Generating audiences..."):

                    demo_rephrased_response, demo_history = hypothetical_audience_gen('demographic', company_name, st.session_state.edited_company_description)
                    behave_rephrased_response, behave_history = hypothetical_audience_gen('behavioral', company_name, st.session_state.edited_company_description)

                    # Extract and combine JSON from both branches
                    demo_json = extract_and_correct_json(demo_rephrased_response)
                    behave_json = extract_and_correct_json(behave_rephrased_response)
                    
                    combined_json = {
                        "demographic": demo_json,
                        "behavioral": behave_json
                    }
                    descriptions = extract_segment_descriptions(combined_json)
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        broadness_scores = list(executor.map(rate_broadness_single_segment, descriptions))
                    combined_json = add_broadness_scores_to_json(combined_json, broadness_scores)

                    st.session_state.extracted_json = combined_json
                    st.json(st.session_state.extracted_json)



        
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
                processed_results = process_audience_segments(st.session_state.extracted_json, presearch_filter={}, top_k=PINECONE_TOP_K)
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