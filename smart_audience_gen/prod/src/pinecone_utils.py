from typing import List, Dict, Any
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
    """Cache the summary in Pinecone."""
    embedding = generate_embedding(initial_prompt)
    id = generate_id(initial_prompt)
    metadata = {
        "domain": domain,
        "data_type": data_type,
        "summary": summary,
        "initial_prompt": initial_prompt
    }
    cache_index.upsert(vectors=[(id, embedding, metadata)])

def get_cached_summary(initial_prompt: str) -> Dict[str, Any] | None:
    """Retrieve cached summary from Pinecone if it exists."""
    embedding = generate_embedding(initial_prompt)
    results = cache_index.query(
        vector=embedding,
        top_k=1,
        include_metadata=True
    )
    
    if results.matches and results.matches[0].score > 0.95:  # Adjust threshold as needed
        print("Cache hit")
        return results.matches[0].metadata
    return None