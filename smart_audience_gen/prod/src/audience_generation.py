import json

from src.api_clients import send_perplexity_message, route_api_call
from src.data_processing import extract_and_correct_json
from typing import Dict, Any, List, Tuple
import streamlit as st

from config.prompts import (
    COMPANY_RESEARCH_PROMPT,
    AUDIENCE_BUILD_PROMPT,
    JSON_AUDIENCE_BUILD_PROMPT,
    INCLUDED_IMPROVING_PROMPT,
    EXCLUDED_IMPROVING_PROMPT,
    REPHRASAL_PROMPT,
    UPDATE_SEGMENTS_PROMPT,
    DELETE_SEGMENTS_PROMPT,
    FEEDBACK_PROMPT,
    COMPARISON_DESCRIPTION
)

def process_message_queue(message_queue, conversation_history):
    results = {}
    
    for step, (prompt_name, prompt, format_args) in enumerate(message_queue, 1):
        formatted_prompt = prompt.format(**format_args) if format_args else prompt
        conversation_history.append({"role": "user", "content": formatted_prompt})
        st.write(prompt_name)
        response = route_api_call('openai', conversation_history)
        conversation_history.append({"role": "assistant", "content": response})
        
        results[prompt_name] = response
    
    return results, conversation_history

def generate_company_description(company_name, conversation_history):
    prompt = COMPANY_RESEARCH_PROMPT.format(company_name=company_name)
    conversation_history.append({"role": "user", "content": prompt})
    
    response = send_perplexity_message(conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    
    return response, conversation_history

def generate_audience_segments(company_name, company_description, conversation_history):
    message_queue = [
        ("Planning audience", AUDIENCE_BUILD_PROMPT, {"company_name": company_name, "company_description": company_description}),
        ("Structuring audience as JSON", JSON_AUDIENCE_BUILD_PROMPT, None),
        ("Improving included segments", INCLUDED_IMPROVING_PROMPT, None),
        ("Improving excluded segments", EXCLUDED_IMPROVING_PROMPT, None),
        ("Rephrasing segments", REPHRASAL_PROMPT, {"company_name": company_name})
    ]

    results, updated_history = process_message_queue(message_queue[:], conversation_history)
    last_key = list(results.keys())[-1]
    return extract_and_correct_json(results[last_key]), updated_history

def generate_audience(company_name, conversation_history):
    """Main function to generate audience"""
    company_description, _ = generate_company_description(company_name, conversation_history)
    audience_segments, final_history = generate_audience_segments(company_name, company_description, [])
    return audience_segments, final_history

def process_user_feedback(user_feedback, conversation_history):
    prompt = FEEDBACK_PROMPT.format(user_feedback=user_feedback)
    
    conversation_history.append({"role": "user", "content": prompt})
    response = route_api_call('openai', conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    
    updated_json = extract_and_correct_json(response)
    return updated_json, conversation_history

def update_audience_segments(
    current_audience: Dict[str, Any],
    selected_segments: List[Tuple[str, str, str]],
    conversation_history: List[Dict[str, str]]
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """
    Update the audience segments based on user selection.
    
    Args:
    current_audience (Dict[str, Any]): The current audience JSON.
    selected_segments (List[Tuple[str, str, str]]): List of selected segments (section, category, description).
    conversation_history (List[Dict[str, str]]): The current conversation history.

    Returns:
    Tuple[Dict[str, Any], List[Dict[str, str]]]: Updated audience JSON and updated conversation history.
    """
    segments_to_remove = get_segments_to_remove(current_audience, selected_segments)
    prompt = format_update_prompt(segments_to_remove)
    
    conversation_history.append({"role": "user", "content": prompt})
    llm_response = route_api_call('openai', conversation_history)
    conversation_history.append({"role": "assistant", "content": llm_response})
    
    updated_audience = extract_and_correct_json(llm_response)
    
    return updated_audience, conversation_history

def get_segments_to_remove(current_audience: Dict[str, Any], selected_segments: List[Tuple[str, str, str]]) -> List[str]:
    """
    Determine which segments need to be removed based on user selection.
    """
    all_segments = set()
    for section in ['included', 'excluded']:
        for category, segments in current_audience['Audience'][section].items():
            for segment in segments:
                all_segments.add((section, category, segment['description']))
    
    selected_set = set(selected_segments)
    return list(all_segments - selected_set)

def format_update_prompt(segments_to_remove: List[Tuple[str, str, str]]) -> str:
    """
    Format the prompt for updating audience segments.
    """
    segments_to_remove_str = "\n".join([f"- [{section}] {category}: {description}" for section, category, description in segments_to_remove])
    
    return UPDATE_SEGMENTS_PROMPT.format(segments_to_remove=segments_to_remove_str)

def delete_unselected_segments(
    current_audience: Dict[str, Any],
    selected_segments: List[Tuple[str, str, str]],
    conversation_history: List[Dict[str, str]]
) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """
    Delete unselected segments from the current audience and update conversation history.
    The actual json is changed, and the conversation history gets a 'fake' user and assistant message
    so that the llm will understand the changes that took place as things progress in the edit apply cycle.
    """
    updated_audience = {"Audience": {"included": {}, "excluded": {}}}
    selected_set = set(selected_segments)

    segments_to_remove = get_segments_to_remove(current_audience, selected_segments)

    for section in ['included', 'excluded']:
        for category, segments in current_audience['Audience'][section].items():
            updated_segments = [
                segment for segment in segments
                if (section, category, segment['description']) in selected_set
            ]
            if updated_segments:
                updated_audience['Audience'][section][category] = updated_segments

    # Format the segments to remove
    deleted_segments_str = "\n".join([
        f"- [{section}] {category}: {description}"
        for section, category, description in segments_to_remove
    ])

    # Create a message about the deletion using the DELETE_SEGMENTS_PROMPT
    deletion_message = DELETE_SEGMENTS_PROMPT.format(deleted_segments=deleted_segments_str)
    
    # Add the deletion message to the conversation history
    conversation_history.append({"role": "user", "content": deletion_message})
    
    # Add the updated audience JSON to the conversation history
    conversation_history.append({
        "role": "assistant",
        "content": json.dumps(updated_audience, indent=2)
    })

    return updated_audience, conversation_history