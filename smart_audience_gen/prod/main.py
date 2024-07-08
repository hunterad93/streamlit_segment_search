import streamlit as st
import json
from src.api_clients import send_perplexity_message, send_groq_message
from src.audience_processing import process_audience_segments, summarize_segments, extract_and_correct_json
from src.report_generation import generate_audience_report
from config import AUDIENCE_BUILD_PROMPT, JSON_AUDIENCE_BUILD_PROMPT, INCLUDED_IMPROVING_PROMPT, EXCLUDED_IMPROVING_PROMPT, COMPANY_RESEARCH_PROMPT

def edit_audience_json():
    if 'edited_json' not in st.session_state:
        st.session_state.edited_json = st.session_state.extracted_json.copy()
    
    edited_data = st.session_state.edited_json
    
    for category in ['included', 'excluded']:
        st.subheader(f"{category.capitalize()} Segments")
        
        category_keys = list(edited_data['Audience'][category].keys())
        
        for group in category_keys:
            st.write(f"Group: {group}")
            
            if st.button(f"Remove {group} group", key=f"remove_{category}_{group}"):
                del edited_data['Audience'][category][group]
                st.session_state.edited_json = edited_data
                st.experimental_rerun()
            
            else:
                for i, item in enumerate(edited_data['Audience'][category][group]):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        new_description = st.text_input(f"Description for {group} item {i+1}", item['description'], key=f"{category}_{group}_{i}")
                        if new_description != item['description']:
                            item['description'] = new_description
                            st.session_state.edited_json = edited_data
                    with col2:
                        if st.button(f"Remove {group} item {i+1}", key=f"remove_{category}_{group}_{i}"):
                            edited_data['Audience'][category][group].pop(i)
                            st.session_state.edited_json = edited_data
                            st.experimental_rerun()
                
                if st.button(f"Add new item to {group}", key=f"add_{category}_{group}"):
                    edited_data['Audience'][category][group].append({"description": ""})
                    st.session_state.edited_json = edited_data
                    st.experimental_rerun()
        
        new_group = st.text_input(f"Add a new group to {category}", key=f"new_group_{category}")
        if st.button(f"Add new group to {category}", key=f"add_group_{category}"):
            if new_group and new_group not in edited_data['Audience'][category]:
                edited_data['Audience'][category][new_group] = []
                st.session_state.edited_json = edited_data
                st.experimental_rerun()
    
    return edited_data

def main():
    st.set_page_config(layout="wide")  # Use wide layout for more space
    
    st.title("Smart Audience Generator")

    # User input
    company_name = st.text_input("Enter company name:", "Bubba Burgers")

    if 'stage' not in st.session_state:
        st.session_state.stage = 0

    if st.session_state.stage == 0 and st.button("Generate Company Description"):
        company_description = send_perplexity_message(COMPANY_RESEARCH_PROMPT.format(company_name=company_name), [])
        st.session_state.company_description = company_description
        st.session_state.stage = 1

    if st.session_state.stage >= 1:
        # Intervention point 1: Edit company description
        edited_company_description = st.text_area("Edit company description:", st.session_state.company_description, height=300)
        if st.button("Continue with Company Description"):
            st.session_state.edited_company_description = edited_company_description
            st.session_state.stage = 2

    if st.session_state.stage >= 2:
        # Build audience and generate JSON
        if 'extracted_json' not in st.session_state:
            with st.spinner("Generating audience..."):
                ai_response, updated_history = send_groq_message(AUDIENCE_BUILD_PROMPT.format(company_name=company_name, company_description=st.session_state.edited_company_description), [])
                json_audience_build_response, updated_history = send_groq_message(JSON_AUDIENCE_BUILD_PROMPT, updated_history[:])
                improving_included_response, updated_history = send_groq_message(INCLUDED_IMPROVING_PROMPT, updated_history[:])
                improving_excluded_response, updated_history = send_groq_message(EXCLUDED_IMPROVING_PROMPT, updated_history[:])
            
            extracted_json = extract_and_correct_json(improving_excluded_response)
            if extracted_json:
                st.session_state.extracted_json = extracted_json
                st.session_state.stage = 3
            else:
                st.error("Failed to extract valid JSON")
                return

    if st.session_state.stage >= 3:
        # Intervention point 2: Edit extracted JSON
        st.subheader("Edit Audience Segments")
        edited_json = edit_audience_json()
        if st.button("Continue with Edited Segments"):
            st.session_state.final_edited_json = edited_json
            st.session_state.stage = 4

 
    if st.session_state.stage >= 5:
        if 'summary_results' not in st.session_state:
            summary_results = summarize_segments(st.session_state.processed_results)
            st.session_state.summary_results = summary_results
        st.json(st.session_state.summary_results)
        
        if 'audience_report' not in st.session_state:
            audience_report = generate_audience_report(st.session_state.summary_results, company_name)
            st.session_state.audience_report = audience_report
        st.markdown(st.session_state.audience_report[0])
        st.session_state.stage = 6

    if st.session_state.stage >= 6:
        #TODO Add logic for creating actual ttd audience
        if st.button("Continue with Processed Results"):
            st.session_state.stage = 7


if __name__ == "__main__":
    main()