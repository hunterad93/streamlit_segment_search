import streamlit as st
from typing import Dict, Any

from src.ui_components import (
    render_company_input, render_json_diff, render_actual_segments,
    render_audience_report, render_button, render_user_feedback,
    render_segment_selection, render_presearch_filter_option)
from src.state_management import StateManager
from src.data_processing import ensure_dict
from src.audience_generation import generate_audience, process_user_feedback, update_audience_segments, delete_unselected_segments
from src.audience_search import process_audience_segments, summarize_segments, extract_research_inputs
from src.report_generation import generate_audience_report
from src.researcher import generate_segment_summaries
from config.settings import PINECONE_TOP_K

def process_audience_data(extracted_json: Dict[str, Any], use_presearch_filter: bool) -> Dict[str, Any]:
    """Process the extracted audience data."""
    presearch_filter = {"BrandName": "Data Alliance"} if use_presearch_filter else {}
    processed_results = process_audience_segments(extracted_json, presearch_filter=presearch_filter, top_k=PINECONE_TOP_K)
    return summarize_segments(processed_results)

def generate_initial_audience(company_name: str, conversation_history: list) -> None:
    """Generate the initial audience based on company name and conversation history."""
    with st.spinner("Generating audience..."):
        audience_segments, updated_history = generate_audience(company_name, conversation_history)
        StateManager.update(
            extracted_audience_json=audience_segments,
            conversation_history=updated_history,
            stage=1
        )


def handle_user_feedback(audience_json: Dict[str, Any]) -> None:
    """Handle user feedback on the audience segments."""
    user_feedback = render_user_feedback()
    if render_button("Apply Feedback"):
        with st.spinner("Applying feedback..."):
            StateManager.update(old_audience_json=audience_json)
            updated_json, updated_history = process_user_feedback(
                user_feedback,
                StateManager.get('conversation_history')
            )
            StateManager.update(
                extracted_audience_json=updated_json,
                conversation_history=updated_history,
                summary_results=None,
                audience_report=None,
                final_report=None,
                stage=1
            )
        st.success("Feedback applied successfully.")
        st.rerun()

def handle_segment_selection(audience_json: Dict[str, Any]) -> None:
    """Handle the selection of segments by the user."""
    selected_segments = render_segment_selection(audience_json)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if render_button("Delete and Replace Unselected Segments"):
            with st.spinner("Updating audience segments..."):
                updated_json, updated_history = update_audience_segments(
                    audience_json,
                    selected_segments,
                    StateManager.get('conversation_history')  # Use get() method here
                )
                StateManager.update(
                    old_audience_json=audience_json,
                    extracted_audience_json=updated_json,
                    conversation_history=updated_history,
                    summary_results=None,
                    audience_report=None,
                    final_report=None,
                    stage=1
                )
            st.success("Audience segments updated successfully.")
            st.rerun()
    with col2:
        if render_button("Delete Unselected Segments"):
            with st.spinner("Deleting unselected segments..."):
                updated_json, updated_history = delete_unselected_segments(
                    audience_json, 
                    selected_segments,
                    StateManager.get('conversation_history')  # Use get() method here
                )
                StateManager.update(
                    old_audience_json=audience_json,
                    extracted_audience_json=updated_json,
                    conversation_history=updated_history,
                    summary_results=None,
                    audience_report=None,
                    final_report=None,
                    stage=1
                )
            st.success("Unselected segments deleted successfully.")
            st.rerun()

def process_and_render_segments() -> None:
    """Process and render the audience segments."""
    use_presearch_filter = StateManager.get('use_presearch_filter')
    
    with st.spinner("Processing audience segments..."):
        if not StateManager.get('summary_results'):
            summary_results = process_audience_data(
                ensure_dict(StateManager.get('extracted_audience_json')),
                use_presearch_filter
            )
            StateManager.update(summary_results=summary_results)
    
    render_actual_segments(StateManager.get('summary_results'))
    
    if not StateManager.get('audience_report'):
        with st.spinner("Generating audience report..."):
            audience_report, updated_history = generate_audience_report(
                StateManager.get('summary_results'), 
                StateManager.get('company_name'), 
                StateManager.get('conversation_history')
            )
            StateManager.update(
                audience_report=audience_report,
                conversation_history=updated_history
            )
    
    render_audience_report(StateManager.get('audience_report'))

def generate_methodology_report() -> None:
    """Generate data collection methodology summaries."""
    with st.spinner("Generating data collection methodology summaries..."):
        segments = extract_research_inputs(StateManager.get('summary_results'))
        segment_summaries = generate_segment_summaries(segments)
        st.json(segment_summaries)

def main() -> None:
    """Main function to run the Streamlit app."""
    st.set_page_config(layout="wide")
    
    # Initialize or reset state for new sessions
    if 'session_id' not in st.session_state:
        StateManager.reset()
    
    st.title("Smart Audience Generator")

    new_company_name = render_company_input()
    
    if render_button("Generate Audience"):
        StateManager.reset()
        StateManager.update(company_name=new_company_name)
        generate_initial_audience(StateManager.get('company_name'), StateManager.get('conversation_history'))

    if StateManager.get('stage') >= 1:
        audience_json = ensure_dict(StateManager.get('extracted_audience_json'))
        
        handle_segment_selection(audience_json)
        
        if StateManager.get('old_audience_json'):
            render_json_diff(StateManager.get('old_audience_json'), audience_json)
        
        handle_user_feedback(audience_json)
        
        # Add the presearch filter option here
        use_presearch_filter = render_presearch_filter_option()
        StateManager.update(use_presearch_filter=use_presearch_filter)
        
        if render_button("Search Actual Segments"):
            StateManager.update(
                summary_results=None,
                audience_report=None,
                final_report=None,
                stage=2
            )
            st.rerun()

    if StateManager.get('stage') >= 2:
        process_and_render_segments()

        if render_button("Generate Methodology Report"):
            generate_methodology_report()

if __name__ == "__main__":
    main()