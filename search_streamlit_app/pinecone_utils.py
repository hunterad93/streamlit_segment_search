from pinecone import Pinecone
from config import PINECONE_API_KEY, PINECONE_INDEX_NAME
from typing import List, Dict, Any

pc = Pinecone(api_key=PINECONE_API_KEY)
index = pc.Index(PINECONE_INDEX_NAME)

def query_pinecone(query_embedding: List[float], top_k: int, presearch_filter: Dict[str, Any] = {}) -> Dict[str, Any]:
    """Query Pinecone index with the given embedding."""
    results = index.query(
        vector=query_embedding,
        filter=presearch_filter,
        top_k=top_k,
        include_metadata=True
    )
    return results