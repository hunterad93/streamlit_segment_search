import streamlit as st
from typing import Dict, Any
import time
import json


from src.ui_components import (
    render_company_input, render_json_diff, render_actual_segments,
    render_audience_report, render_button, render_user_feedback,
    render_segment_selection, render_optimization_strategy_dropdown, render_segment_details)
from src.state_management import StateManager
from src.data_processing import ensure_dict, validate_audience_segments
from src.audience_generation import generate_audience, process_user_feedback, update_audience_segments, delete_unselected_segments
from src.audience_search import process_audience_segments, summarize_segments, extract_research_inputs
from src.report_generation import generate_audience_report
from src.researcher import generate_segment_summaries
from config.settings import PINECONE_TOP_K
from config.prompts import REDUCE_PROMPT, EXPAND_PROMPT

def process_audience_data(extracted_json: Dict[str, Any], use_presearch_filter: bool) -> Dict[str, Any]:
    """Process the extracted audience data."""
    presearch_filter = {"BrandName": "Data Alliance"} if use_presearch_filter else {}
    processed_results = process_audience_segments(extracted_json, presearch_filter=presearch_filter, top_k=PINECONE_TOP_K, optimization_strategy=StateManager.get('optimization_strategy'))
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
    feedback = render_user_feedback()
    if feedback and feedback != StateManager.get('last_feedback'):
        with st.spinner("Applying feedback..."):
            StateManager.update(
                last_feedback=feedback
            )
            updated_json, updated_history = process_user_feedback(
                feedback,
                StateManager.get('conversation_history')
            )
            StateManager.update(
                old_audience_json=audience_json,
                extracted_audience_json=updated_json,
                conversation_history=updated_history,
                post_search_results=None,
                summary_results=None,
                audience_report=None,
                final_report=None,
                stage=1
            )
            if validate_audience_segments((updated_json)):
                st.success("Feedback applied successfully.")
                st.rerun()

def handle_segment_selection(audience_json: Dict[str, Any]) -> None:
    """Handle the selection of segments by the user."""
    selected_segments = render_segment_selection(audience_json)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if render_button("Delete and Replace Unselected Segments"):
            with st.spinner("Updating audience segments..."):
                updated_json, updated_history = update_audience_segments(
                    audience_json,
                    selected_segments,
                    StateManager.get('conversation_history')
                )
                StateManager.update_audience_segments(audience_json, updated_json, updated_history)
                if validate_audience_segments(updated_json):
                    st.success("Audience segments updated successfully.")
                    st.rerun()
    
    with col2:
        if render_button("Delete Unselected Segments"):
            with st.spinner("Deleting unselected segments..."):
                updated_json, updated_history = delete_unselected_segments(
                    audience_json, 
                    selected_segments,
                    StateManager.get('conversation_history')
                )
                StateManager.update_audience_segments(audience_json, updated_json, updated_history)
                if validate_audience_segments(updated_json):
                    st.success("Unselected segments deleted successfully.")
                    st.rerun()
    
    with col3:
        if render_button("Reduce Segments"):
            with st.spinner("Reducing segments..."):
                updated_json, updated_history = process_user_feedback(
                    REDUCE_PROMPT,
                    StateManager.get('conversation_history')
                )
                StateManager.update_audience_segments(audience_json, updated_json, updated_history)
                if validate_audience_segments(updated_json):
                    st.success("Segments reduced successfully.")
                    st.rerun()
    
    with col4:
        if render_button("Expand Reach"):
            with st.spinner("Expanding reach..."):
                updated_json, updated_history = process_user_feedback(
                    EXPAND_PROMPT,
                    StateManager.get('conversation_history')
                )
                StateManager.update_audience_segments(audience_json, updated_json, updated_history)
                if validate_audience_segments(updated_json):
                    st.success("Reach expanded successfully.")
                    st.rerun()

def process_and_render_segments() -> None:
    if StateManager.get('post_search_results') is None:
        """Process and render the audience segments."""
        use_presearch_filter = StateManager.get('use_presearch_filter')
        
        with st.spinner("Searching across 504,311 audience segments for best matches..."):
            post_search_results = process_audience_data(
                ensure_dict(StateManager.get('extracted_audience_json')),
                use_presearch_filter
            )
            StateManager.update(post_search_results=post_search_results)
    
    render_actual_segments(StateManager.get('post_search_results'))
    
    
    if not StateManager.get('audience_report'):
        with st.spinner("Generating audience report..."):
            audience_report = generate_audience_report(
                StateManager.get('post_search_results'), 
                StateManager.get('company_name'), 
                StateManager.get('conversation_history')
            )
            StateManager.update(
                audience_report=audience_report
            )
    
    render_audience_report(StateManager.get('audience_report'))

def generate_methodology_report() -> None:
    """Generate data collection methodology summaries."""
    with st.spinner("Generating data collection methodology summaries..."):
        segments = extract_research_inputs(StateManager.get('post_search_results'))
        segment_summaries = generate_segment_summaries(segments)
        render_segment_details(segment_summaries)

def main() -> None:
    """Main function to run the Streamlit app."""
    st.set_page_config(layout="wide")

    password = st.text_input("Enter password:", type="password")
    if password != st.secrets["app_password"]:  # Ensure this key exists in your secrets
        st.error("Incorrect password. Please try again.")
        return  # Exit the main function if the password is incorrect
    
    # Initialize or reset state for new sessions
    if 'session_id' not in st.session_state:
        StateManager.reset()
    
    st.title("Smart Audience Generator")

    new_company_name = render_company_input()
    
    if render_button("Generate Audience"):
        StateManager.update(
            stage=0,
            company_name="",
            extracted_audience_json=None,
            old_audience_json=None,
            conversation_history=[],
            user_comment="",
            summary_results=None,
            audience_report=None,
            final_report=None,
            use_presearch_filter=False,
            post_search_results=None,
            state_backup=None,
            user_feedback=""
        )
        StateManager.update(company_name=new_company_name)
        generate_initial_audience(StateManager.get('company_name'), StateManager.get('conversation_history'))


    if StateManager.get('stage') >= 1:
        try:
            handle_segment_selection(ensure_dict(StateManager.get('extracted_audience_json')))
            
            if StateManager.get('old_audience_json'):
                render_json_diff(StateManager.get('old_audience_json'), ensure_dict(StateManager.get('extracted_audience_json')))
            
            handle_user_feedback(ensure_dict(StateManager.get('extracted_audience_json')))

        except Exception as e:
            print(f"An error occurred during feedback handling: {str(e)}")
            st.error(f"An error occurred during feedback handling: {str(e)}")
            StateManager.restore_backup()
            st.warning("State is reverting to the last known valid state. Try a different command.")
            time.sleep(5)
            st.rerun()
        
        # Add the optimization strategy dropdown here
        optimization_strategy = render_optimization_strategy_dropdown()
        if optimization_strategy != StateManager.get('optimization_strategy'):
            StateManager.update(
                optimization_strategy=optimization_strategy,
                stage=1,
                post_search_results=None
            )

        
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