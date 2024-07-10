import re
from typing import List, Dict
import concurrent.futures
from tenacity import retry, stop_after_attempt, wait_exponential
import pandas as pd

from config import NON_US_LOCATIONS, RERANK_PROMPT, MAX_RERANK_WORKERS, RELEVANCE_THRESHOLD, RERANK_TOP_K, FALLBACK_TOP_K, RERANKER_MODEL
from .api_clients import openai_client

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
            score = float(match.group()) / 10  # Normalize to 0-1 range
            return max(0, min(score, 1))  # Ensure score is between 0 and 1
        else:
            raise ValueError("No number found in response")
    except ValueError as e:
        print(f"Error parsing score. Error: {str(e)}")
        return 0

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=60))
def gpt_score_relevance(query: str, doc: str) -> float:
    """
    Score the relevance of a document to the query using GPT-3.5.
    Returns a relevance score between 0 and 1.
    """
    formatted_rerank_prompt = RERANK_PROMPT.format(
        query=query,
        doc=doc
    )
    response = openai_client.chat.completions.create(
        model=RERANKER_MODEL,
        messages=[{"role": "user", "content": formatted_rerank_prompt}],
        max_tokens=100,
        temperature=0
    )

    result = response.choices[0].message.content.strip()
    return parse_relevance_score(result)

def filter_high_relevance_segments(df: pd.DataFrame, relevance_threshold: float, top_k: int, fallback_k: int) -> pd.DataFrame:
    """
    Filter segments with high relevance scores.
    
    Args:
        df (pd.DataFrame): Input DataFrame containing segments.
        relevance_threshold (float): Minimum relevance score to consider a segment as highly relevant.
        top_k (int): Number of top segments to return if there are highly relevant segments.
        fallback_k (int): Number of top segments to return if there are no highly relevant segments.

    Returns:
        pd.DataFrame: The top 'top_k' segments with a relevance score of 'relevance_threshold' or higher,
        or the top 'fallback_k' segment(s) if none meet that threshold.
        Returns an empty DataFrame if fallback_k is 0 and no segments meet the relevance threshold.
    """
    high_relevance = df[df['relevance_score'] >= relevance_threshold]
    
    if not high_relevance.empty:
        return high_relevance.head(top_k)
    elif fallback_k > 0:
        return df.head(fallback_k)
    else:
        return pd.DataFrame()  # Return an empty DataFrame if fallback_k is 0