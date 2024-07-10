import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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

def create_scatter_plot(data, x_col, y_col, name, hovertemplate):
    """Create a scatter plot trace with correct ID."""
    return go.Scatter(
        x=data[x_col],
        y=data[y_col],
        name=name,
        mode='markers',
        marker=dict(size=8, opacity=0.6),
        text=data['Segment ID'],  # Use the 'id' column from the dataframe
        hovertemplate=hovertemplate
    )

def create_subplot(plot_data, row, col, x_col, y_col, name, hovertemplate, y_axis_type=None):
    """Create a subplot with given data and parameters."""
    trace = create_scatter_plot(plot_data, x_col, y_col, name, hovertemplate)
    fig.add_trace(trace, row=row, col=col)
    
    fig.update_xaxes(title_text="Relevance Score", row=row, col=col)
    fig.update_yaxes(title_text=name, row=row, col=col)
    
    if y_axis_type:
        fig.update_yaxes(type=y_axis_type, row=row, col=col)


def create_visualization(results):
    """Create and display data visualization."""
    st.subheader("Data Visualization")

    plot_data = results.head(500).copy()
    plot_data['CPM Rate'] = plot_data['CPM Rate'].fillna(0)
    plot_data['PercentOfMediaCostRate'] = plot_data['PercentOfMediaCostRate'].fillna(0)

    global fig
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Relevance vs CPM Rate",
                        "Relevance vs Unique User Count",
                        "Relevance vs Percent of Media Cost Rate",
                        "Relevance vs Unique CTV Count"),
        horizontal_spacing=0.15,
        vertical_spacing=0.2
    )

    create_subplot(plot_data, 1, 1, 'Relevance Score', 'CPM Rate',
                   'CPM Rate ($)', '<b>ID: %{text}</b><br>Relevance: %{x:.2f}<br>CPM Rate: $%{y:.2f}')

    create_subplot(plot_data, 1, 2, 'Relevance Score', 'Unique User Count',
                   'User Count', '<b>ID: %{text}</b><br>Relevance: %{x:.2f}<br>User Count: %{y:,}',
                   y_axis_type="log")

    create_subplot(plot_data, 2, 1, 'Relevance Score', 'PercentOfMediaCostRate',
                   '% Media Cost', '<b>ID: %{text}</b><br>Relevance: %{x:.2f}<br>% Media Cost: %{y:.2%}')
    fig.update_yaxes(tickformat='.0%', row=2, col=1)

    create_subplot(plot_data, 2, 2, 'Relevance Score', 'UniqueConnectedTvCount',
                   'Unique CTV Count', '<b>ID: %{text}</b><br>Relevance: %{x:.2f}<br>Unique CTV Count: %{y:.4f}')

    fig.update_layout(
        height=1000, width=1200,
        title_text="Relevance Score Comparisons",
        showlegend=False,
        template="plotly_white"
    )

    min_relevance = plot_data['Relevance Score'].min()
    max_relevance = plot_data['Relevance Score'].max()

    # Add all columns as custom data
    for i in range(1, 3):
        for j in range(1, 3):
            fig.data[2*(i-1)+j-1].customdata = results

    # Enable clicking on the plot
    fig.update_layout(clickmode='event+select')

    # Use Streamlit's plotly_chart with custom_events
    return st.plotly_chart(fig, use_container_width=True, custom_events=['click'])

def style_dataframe(df, combined_scores):
    def color_scale(val):
        if pd.isna(val):
            return 'background-color: rgba(200, 200, 200, 0.3)'  # Gray for NaN values
        normalized = (val - combined_scores.min()) / (combined_scores.max() - combined_scores.min())
        return f'background-color: rgba({int(255 * (1-normalized))}, {int(255 * normalized)}, 0, 0.3)'

    def color_name(val):
        if val == "Highly Likely":
            return 'background-color: rgba(0, 0, 255, 0.3); color: white'  # Dark blue for Highly Likely with opacity .3
        elif val == "Likely":
            return 'background-color: rgba(173, 216, 230, 0.3); color: black'  # Light blue for Likely with opacity .3
        return ''

    df['Relevance Score'] = df['Relevance Score'].apply(lambda x: f'{x:.3f}')

    # Apply the color scaling to the 'Segment Description' column and color to the 'Segment Name' column based on its content
    styled_df = df.style.apply(
        lambda _: [color_scale(score) for score in combined_scores],
        axis=0,
        subset=['Segment Description']
    ).applymap(color_name, subset=['Segment Name'])

    return styled_df

def main():
    st.set_page_config(layout="wide")
    st.title("3rd Party Data Segment Search")
    st.subheader("Describe the audience segment you are looking for in a few words.")

    query = st.text_input("Enter your search query:")
    
    # Add a slider for search depth
    search_depth = 300

    search_button = st.button("Search")

    if search_button and query:
        st.header(f"Search Results for: {query}")
        with st.spinner(f"Searching and ranking top {search_depth} segments..."):
            results = search_and_rank_segments(query, top_k=search_depth)

        st.success("Search completed!")

        st.subheader(f"Top {search_depth} Segments")
        
        # Calculate the combined score without adding it as a visible column
        combined_scores = (results['Relevance Score'] * 10) / (results['CPM Rate'])

        # Define essential columns
        essential_columns = [
            'Segment Name',
            'Brand Name',
            'Segment Description',
            'Relevance Score',
            'Unique User Count',
            'CPM Rate',
            'Segment ID'
        ]
    
        # Ensure all essential columns exist in df
        existing_essential_columns = [col for col in essential_columns if col in results.columns]
        
        # Identify additional columns
        additional_columns = [col for col in results.columns if col not in existing_essential_columns]

        # Create a dataframe with only essential columns
        essential_df = results[existing_essential_columns]

        # Style the essential dataframe
        styled_essential_df = style_dataframe(essential_df, combined_scores)

        # Display the styled essential dataframe
        st.dataframe(styled_essential_df)

        # Create an expander for additional columns
        with st.expander("Show all columns"):
            full_df = results[existing_essential_columns + additional_columns]
            styled_full_df = style_dataframe(full_df, combined_scores)
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