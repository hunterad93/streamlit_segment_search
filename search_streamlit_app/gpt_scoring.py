from openai import OpenAI
import re
from typing import List, Dict
import concurrent.futures
from config import OPENAI_API_KEY, NON_US_LOCATIONS
import pandas as pd

client = OpenAI(api_key=OPENAI_API_KEY)

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

def filter_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates(subset=['Segment Description', 'Segment Name'], keep='first')

def gpt_score_relevance(query: str, doc: str) -> float:
    """
    Score the relevance of a document to the query using GPT-3.5.
    Returns a relevance score between 0 and 1.
    """

    prompt = f"""On a scale of 0 to 100, how similar is the actual segment to the desired segment?

    Desired segment: "{query}"

    Actual segment: "{doc}"

    Provide only a numeric score between 0 and 100, where 0 is not relevant at all and 100 is extremely relevant.
    """

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=100,
        temperature=0
    )

   

    result = response.choices[0].message.content.strip()
    try:
        # Use regex to find the first number in the response
        match = re.search(r'\d+(?:\.\d+)?', result)
        if match:
            score = float(match.group()) / 100  # Normalize to 0-1 range in thousands place
            return max(0, min(score, 1))  # Ensure score is between 0 and 1
        else:
            raise ValueError("No number found in response")
    except ValueError as e:
        print(f"Error parsing score for document: {doc[:50]}... Error: {str(e)}")
        return 0

def gpt_rerank_results(query: str, docs: List[str], max_workers: int = 100) -> Dict[str, float]:
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