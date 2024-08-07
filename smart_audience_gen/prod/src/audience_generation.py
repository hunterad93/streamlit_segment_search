import json

from src.api_clients import send_perplexity_message, route_api_call
from src.data_processing import extract_and_correct_json
from typing import Dict, Any, List, Tuple
import streamlit as st
from config.settings import ONLINE_MODEL
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

# Audience generation functions
def generate_audience(company_name: str, conversation_history: List[Dict[str, str]]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Generate audience segments for a given company."""
    company_description, updated_history = generate_company_description(company_name, conversation_history)
    return generate_audience_segments(company_name, company_description, updated_history)

def generate_company_description(company_name: str, conversation_history: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    """Generate a company description using online Perplexity."""
    prompt = COMPANY_RESEARCH_PROMPT.format(company_name=company_name)
    return append_to_conversation(prompt, 'online_perplexity', conversation_history)

def generate_audience_segments(company_name: str, company_description: str, conversation_history: List[Dict[str, str]]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Generate audience segments based on company information."""
    message_queue = create_audience_message_queue(company_name, company_description)
    results, updated_history = process_message_queue(message_queue, conversation_history)
    last_response = results[list(results.keys())[-1]]
    return extract_and_correct_json(last_response), updated_history

def create_audience_message_queue(company_name: str, company_description: str) -> List[Tuple[str, str, Dict[str, str]]]:
    """Create a queue of messages for audience generation."""
    return [
        ("Planning audience", AUDIENCE_BUILD_PROMPT, {"company_name": company_name, "company_description": company_description}),
        ("Structuring audience as JSON", JSON_AUDIENCE_BUILD_PROMPT, None),
        ("Improving included segments", INCLUDED_IMPROVING_PROMPT, None),
        ("Improving excluded segments", EXCLUDED_IMPROVING_PROMPT, None),
        ("Rephrasing segments", REPHRASAL_PROMPT, {"company_name": company_name})
    ]

# Conversation handling functions
def process_message_queue(message_queue: List[Tuple[str, str, Dict[str, str]]], conversation_history: List[Dict[str, str]]) -> Tuple[Dict[str, str], List[Dict[str, str]]]:
    """Process a queue of messages and update conversation history."""
    results = {}
    for prompt_name, prompt, format_args in message_queue:
        formatted_prompt = prompt.format(**format_args) if format_args else prompt
        response, conversation_history = append_to_conversation(formatted_prompt, 'openai', conversation_history)
        results[prompt_name] = response
        st.write(prompt_name)
    return results, conversation_history

def append_to_conversation(prompt: str, api_type: str, conversation_history: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, str]]]:
    """Append a message to the conversation history and get a response."""
    conversation_history.append({"role": "user", "content": prompt})
    response = route_api_call(api_type, conversation_history)
    conversation_history.append({"role": "assistant", "content": response})
    return response, conversation_history

# Segment manipulation functions
def update_audience_segments(current_audience: Dict[str, Any], selected_segments: List[Tuple[str, str, str]], conversation_history: List[Dict[str, str]]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Update audience segments based on user selection."""
    segments_to_remove = get_segments_to_remove(current_audience, selected_segments)
    prompt = format_update_prompt(segments_to_remove)
    response, updated_history = append_to_conversation(prompt, 'openai', conversation_history)
    return extract_and_correct_json(response), updated_history

def delete_unselected_segments(current_audience: Dict[str, Any], selected_segments: List[Tuple[str, str, str]], conversation_history: List[Dict[str, str]]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Delete unselected segments and update conversation history."""
    updated_audience = create_updated_audience(current_audience, selected_segments)
    segments_to_remove = get_segments_to_remove(current_audience, selected_segments)
    deletion_message = format_deletion_message(segments_to_remove)
    
    conversation_history.append({"role": "user", "content": deletion_message})
    conversation_history.append({"role": "assistant", "content": json.dumps(updated_audience, indent=2)})
    
    return updated_audience, conversation_history

# Helper functions
def get_segments_to_remove(current_audience: Dict[str, Any], selected_segments: List[Tuple[str, str, str]]) -> List[Tuple[str, str, str]]:
    """Determine which segments need to be removed based on user selection."""
    all_segments = set(get_all_segments(current_audience))
    return list(all_segments - set(selected_segments))

def get_all_segments(audience: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """Get all segments from the audience dictionary."""
    segments = []
    for section in ['included', 'excluded']:
        for category, category_segments in audience['Audience'][section].items():
            segments.extend((section, category, segment['description']) for segment in category_segments)
    return segments

def format_update_prompt(segments_to_remove: List[Tuple[str, str, str]]) -> str:
    """Format the prompt for updating audience segments."""
    segments_str = "\n".join(f"- [{section}] {category}: {description}" for section, category, description in segments_to_remove)
    return UPDATE_SEGMENTS_PROMPT.format(segments_to_remove=segments_str)

def create_updated_audience(current_audience: Dict[str, Any], selected_segments: List[Tuple[str, str, str]]) -> Dict[str, Any]:
    """Create an updated audience dictionary based on selected segments."""
    updated_audience = {"Audience": {"included": {}, "excluded": {}}}
    for section, category, description in selected_segments:
        if category not in updated_audience['Audience'][section]:
            updated_audience['Audience'][section][category] = []
        segment = next((s for s in current_audience['Audience'][section][category] if s['description'] == description), None)
        if segment:
            updated_audience['Audience'][section][category].append(segment)
    return updated_audience

def format_deletion_message(segments_to_remove: List[Tuple[str, str, str]]) -> str:
    """Format the deletion message for the conversation history."""
    deleted_segments_str = "\n".join(f"- [{section}] {category}: {description}" for section, category, description in segments_to_remove)
    return DELETE_SEGMENTS_PROMPT.format(deleted_segments=deleted_segments_str)

# User feedback function
def process_user_feedback(user_feedback: str, conversation_history: List[Dict[str, str]]) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    """Process user feedback and update the audience segments."""
    prompt = FEEDBACK_PROMPT.format(user_feedback=user_feedback)
    response, updated_history = append_to_conversation(prompt, 'openai', conversation_history)
    return extract_and_correct_json(response), updated_history