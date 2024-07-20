from typing import List, Dict, Any
from datetime import datetime, timedelta
import hashlib
from config.settings import PINECONE_API_KEY, PINECONE_INDEX_NAME, PINECONE_TOP_K, PINECONE_CACHE_INDEX
from pinecone import Pinecone
from .embedding import generate_embedding

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)
cache_index = pc.Index(PINECONE_CACHE_INDEX)

def generate_id(text: str) -> str:
    """Generate a hash ID from the given text."""
    return hashlib.sha256(text.encode()).hexdigest()

def query_pinecone(query_embedding: List[float], top_k: int = PINECONE_TOP_K, presearch_filter: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Query Pinecone index with the given embedding."""
    results = index.query(
        vector=query_embedding,
        filter=presearch_filter,
        top_k=top_k,
        include_metadata=True
    )
    return results

def cache_summary(domain: str, data_type: str, initial_prompt: str, summary: str):
    """Cache the summary in Pinecone with a timestamp."""
    embedding = generate_embedding(initial_prompt)
    id = generate_id(initial_prompt)
    current_timestamp = int(datetime.now().timestamp())
    metadata = {
        "domain": domain,
        "data_type": data_type,
        "summary": summary,
        "initial_prompt": initial_prompt,
        "timestamp": current_timestamp
    }
    cache_index.upsert(vectors=[(id, embedding, metadata)])

def get_cached_summary(initial_prompt: str):
    """Retrieve a cached summary from Pinecone, filtering for recent entries."""
    embedding = generate_embedding(initial_prompt)
    
    
    # Query Pinecone with the embedding and timestamp filter
    results = query_pinecone(
        query_embedding=embedding,
        top_k=1,
        presearch_filter={
            "timestamp": {"$gte": int((datetime.now() - timedelta(days=30)).timestamp())}
        }
    )

    if results['matches'] and results['matches'][0]['score'] > 0.95:
        return results['matches'][0]['metadata']
    return None
