import streamlit as st
from src.ui_utils import get_json_diff


def render_company_input():
    return st.text_input("Enter company name:", "Bubba Burgers")

def render_user_feedback():
    return st.text_area("Provide feedback on the audience segments:", key="user_feedback")

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