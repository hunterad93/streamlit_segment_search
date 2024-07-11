from config.settings import EMBEDDING_MODEL
from .api_clients import openai_client

def generate_embedding(text: str) -> list[float]:
    """Generate an embedding for the given text."""
    response = openai_client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=[text],
        encoding_format="float",
        dimensions=256
    )
    return response.data[0].embedding