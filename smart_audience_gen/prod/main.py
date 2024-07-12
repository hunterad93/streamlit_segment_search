import streamlit as st
from src.ui_components import (
    render_company_input,
    render_json_output,
    render_actual_segments,
    render_audience_report,
    render_button
)
from src.state_management import state
from src.audience_generation import generate_audience
from src.audience_processing import process_audience_segments, summarize_segments
from src.report_generation import generate_audience_report
from config.settings import PINECONE_TOP_K

def process_audience_data(extracted_json):
    processed_results = process_audience_segments(extracted_json, presearch_filter={}, top_k=PINECONE_TOP_K)
    summary_results = summarize_segments(processed_results)
    return summary_results

def main():
    st.set_page_config(layout="wide")
    st.title("Smart Audience Generator")

    # Always show the company input field
    new_company_name = render_company_input()
    
    if render_button("Generate Audience"):
        with st.spinner("Generating audience..."):
            # Reset state if company name has changed
            if new_company_name != state.company_name:
                state.reset()
            
            state.company_name = new_company_name
            
            # Generate audience
            audience_segments, updated_history = generate_audience(state.company_name, state.conversation_history)
            
            # Update state
            state.update(
                extracted_audience_json=audience_segments,
                conversation_history=updated_history
            )
            state.stage = 1  # Ensure we're at stage 1 after generation

    if state.stage >= 1:
        render_json_output(state.extracted_audience_json)
        
        if render_button("Search Actual Segments"):
            state.summary_results = None  # Reset summary_results to force reprocessing
            state.audience_report = None  # Reset audience_report as it will be based on new summary
            state.increment_stage()
            st.rerun()

    if state.stage >= 2:
        with st.spinner("Processing audience segments..."):
            if not state.summary_results:
                summary_results = process_audience_data(state.extracted_audience_json)
                state.update(summary_results=summary_results)
        
        render_actual_segments(state.summary_results)
        
        if not state.audience_report:
            with st.spinner("Generating audience report..."):
                audience_report, updated_history = generate_audience_report(
                    state.summary_results, 
                    state.company_name, 
                    state.conversation_history
                )
                state.update(
                    audience_report=audience_report,
                    conversation_history=updated_history
                )
        
        render_audience_report(state.audience_report)

if __name__ == "__main__":
    main()