import streamlit as st
import pandas as pd
from embedding import generate_embedding
from pinecone_utils import query_pinecone
from data_processing import results_to_dataframe
from gpt_scoring import gpt_rerank_results, filter_non_us, filter_duplicates

def search_and_rank_segments(query: str, presearch_filter: dict = {}, top_k: int = 250) -> pd.DataFrame:
    """Search and rank segments based on the given query."""
    query_embedding = generate_embedding(query)
    query_results = query_pinecone(query_embedding, top_k, presearch_filter)
    df = results_to_dataframe(query_results)
    df = filter_non_us(df)
    df = df.sort_values('CPM Rate', ascending=True)
    df = filter_duplicates(df)
    segment_descriptions = df['Segment Description'].tolist()
    confidence_scores = gpt_rerank_results(query, segment_descriptions)
    
    df['Relevance Score'] = df['Segment Description'].map(lambda x: confidence_scores.get(x, 0.0))
    df_sorted = df.sort_values(['Relevance Score', 'CPM Rate'], 
                               ascending=[False, True]).reset_index(drop=True)
    return df_sorted

def style_dataframe(df, segment_scores):
    def color_scale(val):
        if pd.isna(val):
            return 'background-color: rgba(200, 200, 200, 0.3)'  # Gray for NaN values
        normalized = (val - segment_scores.min()) / (segment_scores.max() - segment_scores.min())
        return f'background-color: rgba({int(255 * (1-normalized))}, {int(255 * normalized)}, 0, 0.3)'

    def color_name(val):
        if val == "Highly Likely":
            return 'background-color: rgba(0, 0, 255, 0.3); color: white'  # Dark blue for Highly Likely with opacity .3
        elif val == "Likely":
            return 'background-color: rgba(173, 216, 230, 0.3); color: black'  # Light blue for Likely with opacity .3
        return ''

    df['Relevance Score'] = df['Relevance Score'].apply(lambda x: f'{x:.3f}')

    # Apply the color scaling to both 'Segment Description' and 'Combined Score' columns
    styled_df = df.style.apply(
        lambda _: [color_scale(score) for score in segment_scores],
        axis=0,
        subset=['Segment Description', 'Segment Score']
    ).applymap(color_name, subset=['Segment Name'])

    return styled_df

def main():
    st.set_page_config(layout="wide")

    password = st.text_input("Enter password:", type="password")
    if password != st.secrets["app_password"]:  # Ensure this key exists in your secrets
        st.error("Incorrect password. Please try again.")
        return  # Exit the main function if the password is incorrect

    st.title("3rd Party Data Segment Search")
    st.subheader("Describe the audience segment you are looking for in a few words.")
    st.subheader("Note: 'Segment Score' takes into account both segment cost and relevance score to desired segment, green/red shades are determined by this score.")

    query = st.text_input("Enter your search query:")
    
    # Add a slider for search depth
    search_depth = 300

    search_button = st.button("Search")

    if search_button and query:
        st.header(f"Search Results for: {query}")
        with st.spinner(f"Searching and ranking top segments..."):
            results = search_and_rank_segments(query, top_k=search_depth)

        st.success("Search completed!")

        st.subheader(f"Top {search_depth} Segments")
        
        # Calculate the segment score without adding it as a visible column
        segment_scores = (results['Relevance Score'] * 10) / (results['CPM Rate'])

        # Calculate the segment score and add it as a visible column
        results['Segment Score'] = (results['Relevance Score'] * 10) / results['CPM Rate']
        results['Segment Score'] = results['Segment Score'].round(3)

        # Define essential columns
        essential_columns = [
            'Segment Name',
            'Brand Name',
            'Segment Description',
            'Segment Score',
            'Relevance Score',
            'CPM Rate',
            'Unique User Count',
            'Segment ID'
 
        ]
    
        # Ensure all essential columns exist in df
        existing_essential_columns = [col for col in essential_columns if col in results.columns]
        
        # Identify additional columns
        additional_columns = [col for col in results.columns if col not in existing_essential_columns]

        # Create a dataframe with only essential columns
        essential_df = results[existing_essential_columns]

        # Style the essential dataframe
        styled_essential_df = style_dataframe(essential_df, segment_scores)

        # Display the styled essential dataframe
        st.dataframe(styled_essential_df)

        # Create an expander for additional columns
        with st.expander("Show all columns"):
            full_df = results[existing_essential_columns + additional_columns]
            styled_full_df = style_dataframe(full_df, segment_scores)
            st.dataframe(styled_full_df)
        
        

        # Create and display data visualization
        # create_visualization(results)

        # csv = results.to_csv(index=False)
        # st.download_button(
        #     label="Download results as CSV",
        #     data=csv,
        #     file_name="top_500_segments.csv",
        #     mime="text/csv"
        # )

if __name__ == "__main__":
    main()