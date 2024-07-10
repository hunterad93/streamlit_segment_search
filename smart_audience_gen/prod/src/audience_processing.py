import streamlit as st
from typing import Dict, List
import pandas as pd
import concurrent.futures
import json
from config import RELEVANCE_THRESHOLD, RERANK_TOP_K, FALLBACK_TOP_K
from .data_processing import results_to_dataframe
from .embedding import generate_embedding
from .pinecone_utils import query_pinecone
from .segment_processing import gpt_score_relevance, filter_non_us, filter_high_relevance_segments

def process_segment_batch(query: str, batch: List[Dict]) -> List[Dict]:
    """Process a batch of segments concurrently."""
    with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
        futures = [executor.submit(process_single_segment, query, segment) for segment in batch]
        return [future.result() for future in concurrent.futures.as_completed(futures)]

def process_single_segment(query: str, segment: Dict) -> Dict:
    """Process a single segment."""
    relevance_score = gpt_score_relevance(query, segment['raw_string'])
    return {**segment, 'relevance_score': relevance_score}

def find_top_k_high_relevance(query: str, presearch_filter: dict, top_k: int, high_relevance_count: int) -> pd.DataFrame:
    """
    Search and rank segments based on the given query, processing in batches of 10 using concurrent threads.
    
    Args:
        query (str): The search query.
        presearch_filter (dict): Filter to apply before searching.
        top_k (int): Maximum number of results to retrieve from Pinecone.
        high_relevance_count (int): Number of high-relevance results (score >= RELEVANCE_THRESHOLD) to find before stopping.
    
    Returns:
        pd.DataFrame: Sorted dataframe of relevant segments.
    """
    query_embedding = generate_embedding(query)
    query_results = query_pinecone(query_embedding, top_k, presearch_filter)
    df = results_to_dataframe(query_results)
    df = filter_non_us(df)
    
    high_relevance_segments = []
    high_relevance_found = 0
    
    for i in range(0, len(df), 100):
        batch = df.iloc[i:i+100].to_dict('records')
        processed_batch = process_segment_batch(query, batch)
        
        for segment in processed_batch:
            high_relevance_segments.append(segment)
            if segment['relevance_score'] >= RELEVANCE_THRESHOLD:
                high_relevance_found += 1
                print('found one')
                if high_relevance_found >= high_relevance_count:
                    break
        
        if high_relevance_found >= high_relevance_count:
            break
    
    result_df = pd.DataFrame(high_relevance_segments)
    result_df = result_df.sort_values(['relevance_score', 'CPMRateInAdvertiserCurrency_Amount', 'UniqueUserCount'], 
                                      ascending=[False, True, False]).reset_index(drop=True)
    return result_df


def process_audience_segments(audience_json, presearch_filter, top_k):
    results = {'Audience': {}}
    audience_json = json.loads(audience_json)
    total_items = sum(len(descriptions) for category in ['included', 'excluded'] 
                      for descriptions in audience_json['Audience'][category].values())
    
    progress_bar = st.progress(0)
    processed_items = 0

    for category in ['included', 'excluded']:
        results['Audience'][category] = {}
        for group, descriptions in audience_json['Audience'][category].items():
            group_results = []
            for item in descriptions:
                query = item['description']
                df = find_top_k_high_relevance(query, top_k=top_k)
                df = filter_non_us(df)
                relevant_segments = filter_high_relevance_segments(df, relevance_threshold=RELEVANCE_THRESHOLD, top_k=RERANK_TOP_K, fallback_k=FALLBACK_TOP_K).to_dict('records')
                group_results.append({
                    'description': query,
                    'top_k_segments': relevant_segments
                })
                processed_items += 1
                progress_bar.progress(processed_items / total_items)
            results['Audience'][category][group] = group_results
    
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
                for segment in item['top_k_segments']:
                    summarized_segment = {
                        'raw_string': segment['raw_string']
                    }
                    summarized_segments.append(summarized_segment)
                group_results.append({
                    'description': item['description'],
                    'top_k_segments': summarized_segments
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
                for segment in item['top_k_segments']:
                    segment_info.append({
                        'raw_string': segment['raw_string'],
                        'BrandName': segment.get('BrandName', '')
                    })

    return segment_info