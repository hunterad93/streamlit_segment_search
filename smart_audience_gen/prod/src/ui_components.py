import streamlit as st

def render_company_input():
    return st.text_input("Enter company name:", "Bubba Burgers")

def render_json_output(data):
    st.subheader("Generated Hypothetical Audience Segments")
    st.json(data)

def render_actual_segments(data):
    st.subheader("Actual Segments")
    st.json(data)

def render_audience_report(report):
    st.subheader("Audience Report")
    st.markdown(report)

def render_button(label):
    return st.button(label)