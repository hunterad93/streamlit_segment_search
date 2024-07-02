from openai import OpenAI
from pinecone import Pinecone
import pandas as pd
import json
import concurrent.futures
import re
import streamlit as st
from typing import List, Dict

# Initialize clients using Streamlit secrets
openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
pc = Pinecone(api_key=st.secrets["PINECONE_API_KEY"])
index = pc.Index("3rd-party-data-v2")

# Constants
EMBEDDING_MODEL = "text-embedding-3-large"
CHAT_MODEL = "gpt-4o"

def generate_embedding(text):
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text],
        encoding_format="float",
        dimensions=256
    )
    return response.data[0].embedding

def query_pinecone(query_embedding, top_k, presearch_filter={}):
    results = index.query(
        vector=query_embedding,
        filter=presearch_filter,
        top_k=top_k,
        include_metadata=True
    )
    return results

def flatten_dict(d, parent_key='', sep='_'):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def results_to_dataframe(results):
    data = []
    for match in results.get('matches', []):  # Access 'matches' key from results dictionary
        row = {
            'id': match['id'],
            'vector_score': match['score']
        }
        
        # Handle metadata
        metadata = match.get('metadata', {})
        flattened_metadata = flatten_dict(metadata)
        
        # Create a new dictionary to store processed values
        processed_metadata = {}
        
        # Handle potential JSON strings in metadata
        for key, value in flattened_metadata.items():
            if isinstance(value, str):
                try:
                    parsed_value = json.loads(value)
                    if isinstance(parsed_value, dict):
                        processed_metadata.update(flatten_dict(parsed_value, parent_key=key))
                    else:
                        processed_metadata[key] = value
                except json.JSONDecodeError:
                    processed_metadata[key] = value
            else:
                processed_metadata[key] = value
        
        row.update(processed_metadata)
        data.append(row)
    
    df = pd.DataFrame(data)
    return df

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

    response = openai_client.chat.completions.create(
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
    """

    def score_doc(doc):
        return doc, gpt_score_relevance(query, doc)

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        scores = dict(executor.map(score_doc, docs))
    
    return scores

def search_and_rank_segments(query, presearch_filter={}, top_k=500):
    query_embedding = generate_embedding(query)
    
    query_results = query_pinecone(query_embedding, top_k, presearch_filter)
    df = results_to_dataframe(query_results)
    
    raw_strings = df['raw_string'].tolist()
    confidence_scores = gpt_rerank_results(query, raw_strings)
    
    df['relevance_score'] = df['raw_string'].map(lambda x: confidence_scores.get(x, 0.0))
    df_sorted = df.sort_values('relevance_score', ascending=False).reset_index(drop=True)
    
    return df_sorted.head(100)

def main():
    st.title("3rd Party Data Segment Search")
    st.subheader("Describe the audience segment you are looking for in a sentence.")

    query = st.text_input("Enter your search query:")
    search_button = st.button("Search")

    if search_button and query:
        st.header(f"Search Results for: {query}")
        with st.spinner("Searching and ranking segments..."):
            results = search_and_rank_segments(query)

        st.success("Search completed!")

        st.subheader("Top 100 Segments")
        st.dataframe(results)

        csv = results.to_csv(index=False)
        st.download_button(
            label="Download results as CSV",
            data=csv,
            file_name="top_100_segments.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()