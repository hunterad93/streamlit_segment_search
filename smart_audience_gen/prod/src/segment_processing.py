import re
from typing import List, Dict
import concurrent.futures
from tenacity import retry, stop_after_attempt, wait_exponential
import pandas as pd
import streamlit as st
from config.locations import NON_US_LOCATIONS
from config.prompts import RERANK_PROMPT
from config.settings import RERANKER_MODEL, OPEN_ROUTER_RERANK

from .api_clients import openai_client, open_router_client

def filter_non_us(df: pd.DataFrame) -> pd.DataFrame:
    # Compile the pattern once
    pattern = re.compile(r'\b(' + '|'.join(map(re.escape, NON_US_LOCATIONS)) + r')\b', re.IGNORECASE)
    
    # Concatenate relevant columns only
    relevant_columns = ['Name', 'raw_string', 'BrandName', 'id']
    df['concatenated'] = df[relevant_columns].astype(str).agg(' '.join, axis=1)
    
    # Use vectorized operations
    mask = ~df['concatenated'].str.contains(pattern, regex=True)
    
    # Apply the mask and drop the temporary column
    filtered_df = df[mask].drop(columns=['concatenated'])

    filtered_df.sort_values(by=['CPMRateInAdvertiserCurrency_Amount'], ascending=True, inplace=True)

    filtered_df.drop_duplicates(subset=['raw_string', 'Name'], keep='first', inplace=True)
    
    print(f"Filtered out {len(df) - len(filtered_df)} non-US locations")
    
    return filtered_df


def parse_relevance_score(result: str) -> float:
    """
    Parse the relevance score from the GPT response.
    Returns a normalized score between 0 and 1.
    """
    try:
        match = re.search(r'\d+(?:\.\d+)?', result)
        if match:
            score = float(match.group()) / 100  # Normalize to 0-1 range
            return max(0, min(score, 1))  # Ensure score is between 0 and 1
        else:
            raise ValueError("No number found in response")
    except ValueError as e:
        print(f"Error parsing score. Error: {str(e)}")
        return 0

@retry(
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=2, min=10, max=60)
)
def gpt_score_relevance(query: str, doc: str) -> float:
    """
    Score the relevance of a document to the query using GPT-3.5.
    Returns a relevance score between 0 and 1.
    """
    try:
        formatted_rerank_prompt = RERANK_PROMPT.format(
            query=query,
            doc=doc
        )
        response = open_router_client.chat.completions.create(
            model=OPEN_ROUTER_RERANK,
            messages=[{"role": "user", "content": formatted_rerank_prompt}],
            max_tokens=100,
            temperature=0
        )

        result = response.choices[0].message.content.strip()
        return parse_relevance_score(result)
    except Exception as e:
        if is_rate_limit_error(e):
            st.warning(f"Rate limit error occurred: {str(e)}")
            raise  # Re-raise to trigger retry
        else:
            error_message = f"Error in gpt_score_relevance: {str(e)}"
            st.error(error_message)
            return 0  # Return 0 score on error

def process_single_segment(query: str, segment: Dict) -> Dict:
    """Process a single segment."""
    relevance_score = gpt_score_relevance(query, segment['raw_string'])
    return {**segment, 'relevance_score': relevance_score}