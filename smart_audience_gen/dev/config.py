import streamlit as st

EMBEDDING_MODEL = "text-embedding-3-large"
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
PINECONE_API_KEY = st.secrets["PINECONE_API_KEY"]
PINECONE_INDEX_NAME = "3rd-party-data-v2"