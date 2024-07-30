import streamlit as st
import pandas as pd
from embedding import generate_embedding
from pinecone_utils import query_pinecone
from data_processing import (
    results_to_dataframe,
    calculate_segment_score,
    process_dataframe
)
from gpt_scoring import gpt_rerank_results
from ui_components import render_search_interface, render_results

from config import VERTICALS

def search_and_rank_segments(query: str, vertical: str, presearch_filter: dict = {}, top_k: int = 250) -> pd.DataFrame:
    query_embedding = generate_embedding(query)
    query_results = query_pinecone(query_embedding, top_k, presearch_filter)
    df = results_to_dataframe(query_results)
    
    # Initial processing without relevance score
    df = process_dataframe(df, query, vertical)
    
    # Generate relevance scores
    segment_descriptions = df['Segment Description'].tolist()
    confidence_scores = gpt_rerank_results(query, segment_descriptions)
    df['Relevance Score'] = df['Segment Description'].map(lambda x: confidence_scores.get(x, 0.0))
    
    # Calculate final segment score
    df['Segment Score'] = df['Relevance Score'] * df[f'{vertical} Normalized Score'] / 100
    df['Segment Score'] = df['Segment Score'].round(3)
    df['Overall Normalized Score'] = df['Overall Normalized Score'].round(3)
    df[f'{vertical} Normalized Score'] = df[f'{vertical} Normalized Score'].round(3)
    
    return df.sort_values(['Segment Score', 'Relevance Score', 'Overall Normalized Score', 'CPM Rate'], ascending=[False, False, False, True]).reset_index(drop=True)

def main():
    st.set_page_config(layout="wide")

    password = st.text_input("Enter password:", type="password")
    if password != st.secrets["app_password"]:
        st.error("Incorrect password. Please try again.")
        return

    selected_vertical, query, search_depth, search_button = render_search_interface(VERTICALS)

    if search_button and query:
        with st.spinner(f"Searching and ranking top segments..."):
            results = search_and_rank_segments(query, selected_vertical, top_k=search_depth)

        st.success("Search completed!")
        render_results(results, selected_vertical, search_depth)

if __name__ == "__main__":
    main()