import streamlit as st
from src.ui_utils import get_json_diff
import json


def render_company_input():
    return st.text_input("Enter company name or brief campaign desription:", "Bubba Burgers")

def render_user_feedback():
    return st.text_input("Provide feedback on the audience segments:")

def render_apply_feedback_button():
    return st.button("Apply Feedback")

def render_actual_segments(data):
    st.subheader("Actual Segments")
    st.json(data)

def render_audience_report(report):
    st.subheader("Audience Report")
    st.markdown(report)

def render_button(label):
    return st.button(label)

def render_presearch_filter_option() -> bool:
    """Render a radio button for presearch filter option."""
    filter_option = st.radio(
        "Apply presearch filter for Data Alliance?",
        ("No", "Yes"),
        index=0
    )
    return filter_option == "Yes"

def render_segment_selection(audience_json):
    st.subheader("Current Audience Segments")
    selected_segments = []
    
    audience = audience_json['Audience']
    
    col1, col2 = st.columns(2)
    
    for i, section in enumerate(['included', 'excluded']):
        with col1 if i == 0 else col2:
            st.markdown(f"### {section.capitalize()}")
            for category, segments in audience[section].items():
                with st.expander(f"**{category}** ({len(segments)} segments)", expanded=True):
                    for segment in segments:
                        description = segment['description']
                        if st.checkbox(description, value=True, key=f"{section}_{category}_{description}"):
                            selected_segments.append((section, category, description))
    
    return selected_segments

def render_update_segments_button():
    return st.button("Update and Replace Segments")

def render_delete_segments_button():
    return st.button("Delete Segments")

def render_json_output(json_data, old_json):
    st.subheader("Extracted Audience JSON")
    st.json(json_data)
    if old_json is not None:
        render_json_diff(old_json, json_data)

def render_json_diff(old_json, new_json):
    st.subheader("Changes in Audience Segments")
    diff = get_json_diff(old_json, new_json)
    
    if not any(diff.values()):
        st.info("No changes detected in the audience segments.")
        return

    # Display a summary of changes
    total_changes = sum(len(changes) for changes in diff.values())
    st.write(f"Total changes: {total_changes}")

    if diff["added"]:
        with st.expander(f"Added Segments ({len(diff['added'])})", expanded=False):
            for item in diff["added"]:
                st.markdown(f"- {item}")

    if diff["removed"]:
        with st.expander(f"Removed Segments ({len(diff['removed'])})", expanded=False):
            for item in diff["removed"]:
                st.markdown(f"- {item}")

    if diff["changed"]:
        with st.expander(f"Changed Segments ({len(diff['changed'])})", expanded=False):
            for item in diff["changed"]:
                st.markdown(f"- {item}")