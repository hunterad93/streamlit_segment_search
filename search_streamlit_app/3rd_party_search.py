import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from embedding import generate_embedding
from pinecone_utils import query_pinecone
from data_processing import results_to_dataframe
from gpt_scoring import gpt_rerank_results

def search_and_rank_segments(query: str, presearch_filter: dict = {}, top_k: int = 500) -> pd.DataFrame:
    """Search and rank segments based on the given query."""
    query_embedding = generate_embedding(query)
    query_results = query_pinecone(query_embedding, top_k, presearch_filter)
    df = results_to_dataframe(query_results)
    
    raw_strings = df['raw_string'].tolist()
    confidence_scores = gpt_rerank_results(query, raw_strings)
    
    df['relevance_score'] = df['raw_string'].map(lambda x: confidence_scores.get(x, 0.0))
    df_sorted = df.sort_values(['relevance_score', 'CPMRateInAdvertiserCurrency_Amount'], 
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
        text=data['Name'],  # Use the 'id' column from the dataframe
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
    plot_data['CPMRateInAdvertiserCurrency_Amount'] = plot_data['CPMRateInAdvertiserCurrency_Amount'].fillna(0)
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

    create_subplot(plot_data, 1, 1, 'relevance_score', 'CPMRateInAdvertiserCurrency_Amount',
                   'CPM Rate ($)', '<b>ID: %{text}</b><br>Relevance: %{x:.2f}<br>CPM Rate: $%{y:.2f}')

    create_subplot(plot_data, 1, 2, 'relevance_score', 'UniqueUserCount',
                   'User Count', '<b>ID: %{text}</b><br>Relevance: %{x:.2f}<br>User Count: %{y:,}',
                   y_axis_type="log")

    create_subplot(plot_data, 2, 1, 'relevance_score', 'PercentOfMediaCostRate',
                   '% Media Cost', '<b>ID: %{text}</b><br>Relevance: %{x:.2f}<br>% Media Cost: %{y:.2%}')
    fig.update_yaxes(tickformat='.0%', row=2, col=1)

    create_subplot(plot_data, 2, 2, 'relevance_score', 'UniqueConnectedTvCount',
                   'Unique CTV Count', '<b>ID: %{text}</b><br>Relevance: %{x:.2f}<br>Unique CTV Count: %{y:.4f}')

    fig.update_layout(
        height=1000, width=1200,
        title_text="Relevance Score Comparisons",
        showlegend=False,
        template="plotly_white"
    )

    min_relevance = plot_data['relevance_score'].min()
    max_relevance = plot_data['relevance_score'].max()

    # Add all columns as custom data
    for i in range(1, 3):
        for j in range(1, 3):
            fig.data[2*(i-1)+j-1].customdata = results

    # Enable clicking on the plot
    fig.update_layout(clickmode='event+select')

    # Use Streamlit's plotly_chart with custom_events
    return st.plotly_chart(fig, use_container_width=True, custom_events=['click'])

def main():
    st.title("3rd Party Data Segment Search")
    st.subheader("Describe the audience segment you are looking for in a sentence.")

    query = st.text_input("Enter your search query:")
    
    # Add a slider for search depth
    search_depth = st.slider("Search Depth", min_value=100, max_value=1000, value=500, step=100,
                             help="Adjust the number of top results to retrieve and rank, cost is around 1 cent per 250 depth.")

    search_button = st.button("Search")

    if search_button and query:
        st.header(f"Search Results for: {query}")
        with st.spinner(f"Searching and ranking top {search_depth} segments..."):
            results = search_and_rank_segments(query, top_k=search_depth)

        st.success("Search completed!")

        st.subheader(f"Top {search_depth} Segments")
        
        # Calculate the combined score without adding it as a visible column
        combined_scores = (results['relevance_score'] * 10) / (results['CPMRateInAdvertiserCurrency_Amount'])

        # Reorder columns
        desired_order = [
        'Name',
        'BrandName',
        'raw_string',
        'relevance_score',
        'UniqueUserCount',
        'CPMRateInAdvertiserCurrency_Amount'
        ]
    
        # Ensure all columns in desired_order exist in df
        existing_columns = [col for col in desired_order if col in results.columns]
        
        # Add any remaining columns that weren't specified in desired_order
        remaining_columns = [col for col in results.columns if col not in existing_columns]
    
        # Reorder the dataframe
        results = results[existing_columns + remaining_columns]
        
        def color_scale(val):
            if pd.isna(val):
                return 'background-color: rgba(200, 200, 200, 0.3)'  # Gray for NaN values
            normalized = (val - combined_scores.min()) / (combined_scores.max() - combined_scores.min())
            return f'background-color: rgba({int(255 * (1-normalized))}, {int(255 * normalized)}, 0, 0.3)'

        # Apply the color scaling to the 'raw_string' column
        styled_results = results.style.apply(
            lambda _: [color_scale(score) for score in combined_scores],
            axis=0,
            subset=['raw_string']
        )

        # Display the styled dataframe
        st.dataframe(styled_results)

        # Create and display data visualization
        create_visualization(results)

        csv = results.to_csv(index=False)
        st.download_button(
            label="Download results as CSV",
            data=csv,
            file_name="top_500_segments.csv",
            mime="text/csv"
        )

if __name__ == "__main__":
    main()