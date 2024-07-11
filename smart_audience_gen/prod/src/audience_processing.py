import streamlit as st
from typing import Dict, List
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from .data_processing import results_to_dataframe
from .embedding import generate_embedding
from .pinecone_utils import query_pinecone
from .segment_processing import process_single_segment, filter_non_us
from .api_clients import send_groq_message, send_openai_message, select_context
from config import RELEVANCE_THRESHOLD, DEMOGRAPHIC_AUDIENCE_BUILD_PROMPT, JSON_AUDIENCE_BUILD_PROMPT, INCLUDED_IMPROVING_PROMPT, EXCLUDED_IMPROVING_PROMPT, REPHRASAL_PROMPT, BEHAVIORAL_AUDIENCE_BUILD_PROMPT, DEMOGRAPHIC_INCLUDED_IMPROVING_PROMPT

def hypothetical_audience_gen(category: str, company_name: str, company_description: str):
    steps = [
        ("Planning audience", f"{category.capitalize()} Audience: Step 1/5: Planning {category} audience"),
        ("Structuring audience as JSON", f"{category.capitalize()} Audience: Step 2/5: Structuring audience as JSON"),
        ("Improving included segments", f"{category.capitalize()} Audience: Step 3/5: Improving included segments"),
        ("Improving excluded segments", f"{category.capitalize()} Audience: Step 4/5: Improving excluded segments"),
        ("Rephrasing segments", f"{category.capitalize()} Audience: Step 5/5: Rephrasing segments")
    ]
    
    prompts = {
        "demographic": {
            "planning": DEMOGRAPHIC_AUDIENCE_BUILD_PROMPT,
            "structuring": JSON_AUDIENCE_BUILD_PROMPT,
            "included": DEMOGRAPHIC_INCLUDED_IMPROVING_PROMPT,
            "excluded": EXCLUDED_IMPROVING_PROMPT,
            "rephrasing": REPHRASAL_PROMPT
        },
        "behavioral": {
            "planning": BEHAVIORAL_AUDIENCE_BUILD_PROMPT,
            "structuring": JSON_AUDIENCE_BUILD_PROMPT,
            "included": INCLUDED_IMPROVING_PROMPT,
            "excluded": EXCLUDED_IMPROVING_PROMPT,
            "rephrasing": REPHRASAL_PROMPT
        }
    }

    history = []
    for step, (description, status_text) in enumerate(steps):
        st.text(status_text)
        if step == 0:
            prompt = prompts[category]["planning"].format(company_name=company_name, company_description=company_description)
            response, history = send_groq_message(prompt, [])
        else:
            prompt = prompts[category][list(prompts[category].keys())[step]]
            response, history = send_groq_message(prompt, select_context(history, num_first=2, num_recent=7))

    return response, history    

def find_first_high_relevance(query: str, presearch_filter: dict, top_k: int) -> pd.DataFrame:
    query_embedding = generate_embedding(query)
    query_results = query_pinecone(query_embedding, top_k, presearch_filter)
    df = results_to_dataframe(query_results)
    df = filter_non_us(df)
    df = df.sort_values(['vector_score', 'CPMRateInAdvertiserCurrency_Amount', 'UniqueUserCount'], 
                       ascending=[False, True, False]).reset_index(drop=True)

    segments_searched = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_single_segment, query, segment) for segment in df.to_dict('records')]
        
        for future in as_completed(futures):
            processed_segment = future.result()
            segments_searched += 1
            if processed_segment['relevance_score'] >= RELEVANCE_THRESHOLD:
                executor.shutdown(wait=False, cancel_futures=True)
                print(f"Found high-relevance segment after searching {segments_searched} segments")
                return pd.DataFrame([processed_segment])
    
    print(f"No high-relevance segment found after searching {segments_searched} segments")
    return pd.DataFrame()  # Return empty DataFrame if no high-relevance segment found

def process_audience_segments(audience_json, presearch_filter, top_k):
    results = {'demographic': {'Audience': {}}, 'behavioral': {'Audience': {}}}
    audience_json = json.loads(audience_json) if isinstance(audience_json, str) else audience_json

    total_items = sum(
        len(descriptions)
        for category in ['demographic', 'behavioral']
        for inc_exc in ['included', 'excluded']
        for descriptions in audience_json[category]['Audience'][inc_exc].values()
    )
    
    progress_bar = st.progress(0)
    processed_items = 0

    for category in ['demographic', 'behavioral']:
        for inc_exc in ['included', 'excluded']:
            results[category]['Audience'][inc_exc] = {}
            for group, descriptions in audience_json[category]['Audience'][inc_exc].items():
                group_results = []
                for item in descriptions:
                    query = item['description']
                    relevant_segment = find_first_high_relevance(query, presearch_filter, top_k)
                    group_results.append({
                        'description': query,
                        'broadness_score': item.get('broadness_score', 0),
                        'top_k_segments': relevant_segment.to_dict('records') if not relevant_segment.empty else []
                    })
                    processed_items += 1
                    progress_bar.progress(processed_items / total_items)
                results[category]['Audience'][inc_exc][group] = group_results
    
    progress_bar.empty()  # Remove the progress bar when done
    return results

# Adjust the summarize_segments function similarly
def summarize_segments(processed_results):
    summary_json = {'demographic': {'Audience': {}}, 'behavioral': {'Audience': {}}}
    
    for category in ['demographic', 'behavioral']:
        for inc_exc in ['included', 'excluded']:
            summary_json[category]['Audience'][inc_exc] = {}
            for group, descriptions in processed_results[category]['Audience'][inc_exc].items():
                group_results = []
                for item in descriptions:
                    summarized_segments = []
                    for segment in item['top_k_segments']:
                        summarized_segment = {
                            'raw_string': segment['raw_string']
                        }
                        summarized_segments.append(summarized_segment)
                    group_results.append({
                        'description': item['description'],
                        'broadness_score': item.get('broadness_score', 0),
                        'top_k_segments': summarized_segments
                    })
                summary_json[category]['Audience'][inc_exc][group] = group_results
    
    return summary_json


def extract_research_inputs(processed_results: Dict) -> List[Dict[str, str]]:
    segment_info = []

    for category in ['demographic', 'behavioral']:
        for inc_exc in ['included', 'excluded']:
            for group in processed_results[category]['Audience'][inc_exc].values():
                for item in group:
                    for segment in item['top_k_segments']:
                        segment_info.append({
                            'raw_string': segment['raw_string'],
                            'BrandName': segment.get('BrandName', '')
                        })

    return segment_info