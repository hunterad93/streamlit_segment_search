from openai import OpenAI
import re
from typing import List, Dict
import concurrent.futures
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def gpt_score_relevance(query: str, doc: str) -> float:
    """
    Score the relevance of a document to the query using GPT-3.5.
    Returns a relevance score between 0 and 1.
    """
    prompt = f"""On a scale of 0 to 10, how similar is the actual segment to the desired segment?

    Desired segment: "{query}"

    Actual segment: "{doc}"

    Provide only a numeric score between 0 and 10, where 0 is not relevant at all and 10 is extremely relevant.
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
            score = float(match.group()) / 10  # Normalize to 0-1 range
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