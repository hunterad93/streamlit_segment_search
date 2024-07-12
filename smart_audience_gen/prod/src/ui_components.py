import streamlit as st

def render_company_input():
    return st.text_input("Enter company name:", "Bubba Burgers")

def render_company_description(description):
    return st.text_area("Edit company description:", description, height=300)

def render_json_output(data):
    st.subheader("Generated Hypothetical Audience Segments")
    st.json(data)

def render_actual_segments(data):
    st.subheader("Actual Segments")
    st.json(data)

def render_audience_report(report):
    st.subheader("Audience Report")
    st.markdown(report[0])

def render_button(label):
    return st.button(label)