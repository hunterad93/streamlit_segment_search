import streamlit as st
from src.ui_components import (
    render_company_input,
    render_json_output,
    render_json_diff,
    render_actual_segments,
    render_audience_report,
    render_button,
    render_user_feedback,
    render_apply_feedback_button
)
from src.state_management import state
from src.audience_generation import generate_audience, process_user_feedback
from src.audience_processing import process_audience_segments, summarize_segments
from src.report_generation import generate_audience_report
from src.data_processing import extract_and_correct_json
from config.settings import PINECONE_TOP_K

def process_audience_data(extracted_json):
    processed_results = process_audience_segments(extracted_json, presearch_filter={}, top_k=PINECONE_TOP_K)
    summary_results = summarize_segments(processed_results)
    return summary_results

def main():
    st.set_page_config(layout="wide")
    st.title("Smart Audience Generator")

    new_company_name = render_company_input()
    
    if render_button("Generate Audience"):
        with st.spinner("Generating audience..."):
            if new_company_name != state.company_name:
                state.reset()
            
            state.company_name = new_company_name
            
            audience_segments, updated_history = generate_audience(state.company_name, state.conversation_history)
            
            state.update(
                extracted_audience_json=audience_segments,
                old_audience_json=None,  # Reset old JSON when generating new audience
                conversation_history=updated_history,
                summary_results=None,
                audience_report=None
            )
            state.stage = 1

    if state.stage >= 1:
        render_json_output(state.extracted_audience_json, state.old_audience_json)
        
        user_feedback = render_user_feedback()
        if render_apply_feedback_button():
            with st.spinner("Updating audience segments..."):
                state.old_audience_json = state.extracted_audience_json  # Store the current JSON as old
                updated_json, updated_history = process_user_feedback(
                    state.extracted_audience_json,
                    user_feedback,
                    state.conversation_history
                )
                state.update(
                    extracted_audience_json=updated_json,
                    conversation_history=updated_history,
                    summary_results=None,
                    audience_report=None
                )
            st.success("Audience segments updated based on your feedback.")
            st.rerun()
        
        if render_button("Search Actual Segments"):
            state.summary_results = None
            state.audience_report = None
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