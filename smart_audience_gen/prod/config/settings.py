import streamlit as st

# Constants
EMBEDDING_MODEL = "text-embedding-3-large" # Embedding model used to create vectors to search pinecone
PINECONE_INDEX_NAME = "3rd-party-data-v2" # Pinecone index name
PINECONE_CACHE_INDEX = "researcher-cache" # Pinecone cache index name
ONLINE_MODEL = "llama-3-sonar-large-32k-online" # Online model used for company research
OFFLINE_MODEL = "llama-3-sonar-large-32k-chat" # Offline model used for company research
OPENAI_MODEL = "gpt-4o-mini-2024-07-18" # OpenAI model used for audience generation
GROQ_MODEL = "llama3-70b-8192" # Groq model used for audience generation
OPEN_ROUTER_MODEL = "anthropic/claude-3.5-sonnet" # Open Router model used for audience generation # anthropic/claude-3.5-sonnet # meta-llama/llama-3-70b-instruct
OPEN_ROUTER_RERANK = "google/gemma-2-9b-it"
RERANKER_MODEL = "gpt-4o-mini-2024-07-18" # Reranker model used for actual segment searching
API_SELECTOR = 'openai' # 'openai' or 'groq' or 'open_router'

# Parameters
MAX_RERANK_WORKERS = 10 # Max concurrency for search reranking
RELEVANCE_THRESHOLD = .9 # Relevance threshold for search reranking
SECONDARY_RELEVANCE_THRESHOLD = .85 # Secondary relevance threshold for search reranking
RERANK_TOP_K = 3 
FALLBACK_TOP_K = 0
PINECONE_TOP_K = 300
CONTEXT_LENGTH_START = 2 # Number of messages to pass from beginning of conversation
CONTEXT_LENGTH_END = 8 # Number of messages to pass from end of conversation

# API keys
PPLX_API_KEY = st.secrets["PPLX_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
OPEN_ROUTER_KEY = st.secrets["OPEN_ROUTER_KEY"]

