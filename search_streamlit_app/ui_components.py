import streamlit as st
import pandas as pd

def style_dataframe(df, vertical):
    def color_scale(val):
        if pd.isna(val):
            return 'background-color: rgba(200, 200, 200, 0.3)'
        normalized = (val - df['Segment Score'].min()) / (df['Segment Score'].max() - df['Segment Score'].min())
        return f'background-color: rgba({int(255 * (1-normalized))}, {int(255 * normalized)}, 0, 0.3)'

    def format_score(val):
        return f'{val:.3f}'

    styled_df = df.style.apply(
        lambda x: pd.Series([color_scale(x['Segment Score'])] * len(x), index=x.index),
        axis=1,
        subset=['Segment Description', 'Segment Score', 'Overall Normalized Score', f'{vertical} Normalized Score']
    ).format({
        'Segment Score': format_score,
        'Relevance Score': format_score,
        'Overall Normalized Score': format_score,
        f'{vertical} Normalized Score': format_score
    })

    return styled_df

def render_search_interface(verticals):
    st.title("3rd Party Data Segment Search")
    st.subheader("Note: 'Segment Score' is a composite metric combining z-scores of CPA (lower is better) and CTR (higher is better), along with the relevance score to the desired segment. This score is normalized to a 0-100 range. The green/red shades in the visualization are determined by this score."
)
    selected_vertical = st.selectbox("Select campaign vertical:", verticals)
    query = st.text_input("Describe the audience segment you are looking for in a few words.")
    search_button = st.button("Search")

    return selected_vertical, query, search_button

def render_results(results, selected_vertical):
    st.header(f"Search Results")

    essential_columns = [
        'Segment Name', 'Brand Name', 'Segment Description', 'Segment Score',
        'Relevance Score', 'Overall Normalized Score', f'{selected_vertical} Normalized Score',
        'CPM Rate', 'Overall CPA', 'Overall CTR',
        f'{selected_vertical} CPA', f'{selected_vertical} CTR',
        'Unique User Count', 'Segment ID'
    ]

    filtered_results = results[essential_columns].copy()
    
    st.dataframe(style_dataframe(filtered_results, selected_vertical))

    with st.expander("Show all columns"):
        st.dataframe(style_dataframe(results.copy(), selected_vertical))
        