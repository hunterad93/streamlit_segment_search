import streamlit as st

# Constants
EMBEDDING_MODEL = "text-embedding-3-large"
PINECONE_INDEX_NAME = "3rd-party-data-v2"
ONLINE_MODEL = "llama-3-sonar-large-32k-online"
OFFLINE_MODEL = "llama-3-sonar-large-32k-chat"
OPENAI_MODEL = "gpt-4o"
GROQ_MODEL = "llama3-70b-8192"
RERANKER_MODEL = "gpt-3.5-turbo"

# Parameters
MAX_RERANK_WORKERS = 100
RELEVANCE_THRESHOLD = .9
RERANK_TOP_K = 3
FALLBACK_TOP_K = 0
PINECONE_TOP_K = 200

# API keys
PPLX_API_KEY = st.secrets["PPLX_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]