import streamlit as st
from typing import Dict, List
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from .data_processing import results_to_dataframe
from .embedding import generate_embedding
from .pinecone_utils import query_pinecone
from .segment_processing import process_single_segment, filter_non_us
from config.settings import RELEVANCE_THRESHOLD, MAX_RERANK_WORKERS, SECONDARY_RELEVANCE_THRESHOLD


def find_relevant_segments(query: str, presearch_filter: dict, top_k: int) -> pd.DataFrame:
    query_embedding = generate_embedding(query)
    query_results = query_pinecone(query_embedding, top_k, presearch_filter)
    df = results_to_dataframe(query_results)
    df = filter_non_us(df)
    df = df.sort_values(['vector_score', 'CPMRateInAdvertiserCurrency_Amount', 'UniqueUserCount'], 
                       ascending=[False, True, False]).reset_index(drop=True)

    processed_segments = []
    segments_searched = 0

    with ThreadPoolExecutor(max_workers=MAX_RERANK_WORKERS) as executor:
        futures = [executor.submit(process_single_segment, query, segment) for segment in df.to_dict('records')]
        
        for future in as_completed(futures):
            processed_segment = future.result()
            processed_segments.append(processed_segment)
            segments_searched += 1
            
            if processed_segment['relevance_score'] >= RELEVANCE_THRESHOLD:
                executor.shutdown(wait=False, cancel_futures=True)
                print(f"Found high-relevance segment after searching {segments_searched} segments")
                return pd.DataFrame([processed_segment])
    
    print(f"No high-relevance segment found after searching {segments_searched} segments")
    
    # If no high-relevance segments found, return top 3 segments above secondary threshold
    secondary_segments = [s for s in processed_segments if s['relevance_score'] >= SECONDARY_RELEVANCE_THRESHOLD]
    secondary_segments.sort(key=lambda x: x['relevance_score'], reverse=True)
    top_3_secondary = secondary_segments[:3]
    
    if top_3_secondary:
        print(f"Returning top {len(top_3_secondary)} segments above secondary threshold")
        return pd.DataFrame(top_3_secondary)
    
    return pd.DataFrame()  # Return empty DataFrame if no high-relevance segment found

def process_audience_segments(audience_json, presearch_filter, top_k):
    results = {'Audience': {}}
    total_items = sum(len(descriptions) for category in ['included', 'excluded'] 
                      for descriptions in audience_json['Audience'][category].values())
    
    progress_bar = st.progress(0)
    processed_items = 0

    def process_item(item, category, group):
        query = item['description']
        relevant_segment = find_relevant_segments(query, presearch_filter, top_k)
        return {
            'description': query,
            'ActualSegments': relevant_segment.to_dict('records') if not relevant_segment.empty else [],
            'category': category,
            'group': group
        }

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for category in ['included', 'excluded']:
            results['Audience'][category] = {}
            for group, descriptions in audience_json['Audience'][category].items():
                futures.extend([executor.submit(process_item, item, category, group) for item in descriptions])

        for future in as_completed(futures):
            result = future.result()
            category, group = result['category'], result['group']
            if group not in results['Audience'][category]:
                results['Audience'][category][group] = []
            results['Audience'][category][group].append({
                'description': result['description'],
                'ActualSegments': result['ActualSegments']
            })
            processed_items += 1
            progress_bar.progress(processed_items / total_items)

    progress_bar.empty()  # Remove the progress bar when done
    return results

def summarize_segments(processed_results):
    summary_json = {'Audience': {}}
    
    for category in ['included', 'excluded']:
        summary_json['Audience'][category] = {}
        for group, descriptions in processed_results['Audience'][category].items():
            group_results = []
            for item in descriptions:
                summarized_segments = []
                for segment in item['ActualSegments']:
                    summarized_segment = {
                        'ActualSegment': segment['raw_string'],
                        'BrandName': segment['BrandName']
                    }
                    summarized_segments.append(summarized_segment)
                group_results.append({
                    'description': item['description'],
                    'ActualSegments': summarized_segments
                })
            summary_json['Audience'][category][group] = group_results
    
    return summary_json

def extract_research_inputs(processed_results: Dict) -> List[Dict[str, str]]:
    """
    Extract raw_string and BrandName from all relevant segments in the processed results.

    Args:
    processed_results (Dict): The processed audience results.

    Returns:
    List[Dict[str, str]]: A list of dictionaries containing raw_string and BrandName.
    """
    segment_info = []

    for category in ['included', 'excluded']:
        for group in processed_results['Audience'][category].values():
            for item in group:
                for segment in item['ActualSegments']:
                    segment_info.append({
                        'ActualSegment': segment['ActualSegment'],
                        'BrandName': segment.get('BrandName', '')
                    })

    return segment_info