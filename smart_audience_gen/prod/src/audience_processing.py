import json
import time
from typing import Dict, List
import pandas as pd

from .data_processing import results_to_dataframe, extract_and_correct_json
from .embedding import generate_embedding
from .pinecone_utils import query_pinecone
from .gpt_scoring import gpt_rerank_results, filter_non_us, filter_high_relevance_segments

def search_and_rank_segments(query: str, presearch_filter: dict = {}, top_k: int = 2) -> pd.DataFrame:
    """Search and rank segments based on the given query."""
    query_embedding = generate_embedding(query)
    query_results = query_pinecone(query_embedding, top_k, presearch_filter)
    df = results_to_dataframe(query_results)
    df = filter_non_us(df)
    raw_strings = df['raw_string'].tolist()
    confidence_scores = gpt_rerank_results(query, raw_strings)
    
    df['relevance_score'] = df['raw_string'].map(lambda x: confidence_scores.get(x, 0.0))
    df_sorted = df.sort_values(['relevance_score', 'CPMRateInAdvertiserCurrency_Amount', 'UniqueUserCount'], 
                               ascending=[False, True, False]).reset_index(drop=True)
    return df_sorted


def process_audience_segments(audience_json):
    results = {'Audience': {}}
    for category in ['included', 'excluded']:
        results['Audience'][category] = {}
        for group, descriptions in audience_json['Audience'][category].items():
            group_results = []
            for item in descriptions:
                query = item['description']
                df = search_and_rank_segments(query)
                df = filter_non_us(df)
                relevant_segments = filter_high_relevance_segments(df, relevance_threshold=0.9, top_k=3, fallback_k=0).to_dict('records')
                group_results.append({
                    'description': query,
                    'top_k_segments': relevant_segments
                })
                time.sleep(.01)  # Add a 5-second delay between each iteration
            results['Audience'][category][group] = group_results
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