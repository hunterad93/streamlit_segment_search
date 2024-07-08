import re
from typing import List, Dict
import concurrent.futures
import pandas as pd

from config import NON_US_LOCATIONS, RERANK_PROMPT, MAX_RERANK_WORKERS, RELEVANCE_THRESHOLD, RERANK_TOP_K, FALLBACK_TOP_K, RERANKER_MODEL
from .api_clients import openai_client

def filter_non_us(df: pd.DataFrame) -> pd.DataFrame:
    
    def contains_non_us_location(row):
        concatenated = ' '.join(row.astype(str))
        for location in NON_US_LOCATIONS:
            if re.search(r'\b' + re.escape(location) + r'\b', concatenated, re.IGNORECASE):
                print(f"Filtering out: {concatenated}")
                print(f"Matched location: {location}")
                return False
        return True
    
    return df[df.apply(contains_non_us_location, axis=1)]

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
    try:
        # Use regex to find the first number in the response
        match = re.search(r'\d+(?:\.\d+)?', result)
        if match:
            score = float(match.group()) / 10  # Normalize to 0-1 range
            return max(0, min(score, 1))  # Ensure score is between 0 and 1
        else:
            raise ValueError("No number found in response")
    except ValueError as e:
        print(f"Error parsing score for document: {doc[:50]}... Error: {str(e)}")
        return 0

def gpt_rerank_results(query: str, docs: List[str], max_workers: int = MAX_RERANK_WORKERS) -> Dict[str, float]:
    """
    Rerank documents by scoring each document's relevance to the query using GPT-3.5.
    Uses concurrent.futures to parallelize the scoring process.
    Keeps track of total input tokens.
    """
    total_tokens = 0

    def score_doc(doc):
        nonlocal total_tokens
        total_tokens += len(query.split()) + len(doc.split())
        return doc, gpt_score_relevance(query, doc)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        scores = dict(executor.map(score_doc, docs))
    
    # Calculate and print the number *1000000/50
    token_cost = (total_tokens / 1000000) * 0.5
    print(f"Estimated rerank cost: ${token_cost:.6f}")
    
    return scores

def filter_high_relevance_segments(df: pd.DataFrame, relevance_threshold: float = RELEVANCE_THRESHOLD, top_k: int = RERANK_TOP_K, fallback_k: int = FALLBACK_TOP_K) -> pd.DataFrame:
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