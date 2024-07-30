import pandas as pd
import json
from typing import Dict, Any, List
from ast import literal_eval
import re
import numpy as np
from config import NON_US_LOCATIONS

def calculate_z_scores(df, vertical):
    # Overall Z-scores
    df['Overall CTR Z-score'] = (df['Overall CTR'] - df['Overall CTR'].mean()) / df['Overall CTR'].std()
    df['Overall CPA Z-score'] = (df['Overall CPA'] - df['Overall CPA'].mean()) / df['Overall CPA'].std()
    
    # Vertical-specific Z-scores
    df[f'{vertical} CTR Z-score'] = (df[f'{vertical} CTR'] - df[f'{vertical} CTR'].mean()) / df[f'{vertical} CTR'].std()
    df[f'{vertical} CPA Z-score'] = (df[f'{vertical} CPA'] - df[f'{vertical} CPA'].mean()) / df[f'{vertical} CPA'].std()
    
    return df

def calculate_normalized_scores(df, vertical):
    # Calculate the difference between CTR and CPA z-scores
    df['Overall Score'] = df['Overall CTR Z-score'] - df['Overall CPA Z-score']
    df[f'{vertical} Score'] = df[f'{vertical} CTR Z-score'] - df[f'{vertical} CPA Z-score']

    # Normalize to 0-100 range
    def normalize_to_100(series):
        return (series - series.min()) / (series.max() - series.min()) * 100

    df['Overall Normalized Score'] = normalize_to_100(df['Overall Score'])
    df[f'{vertical} Normalized Score'] = normalize_to_100(df[f'{vertical} Score'])

    return df

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, json.dumps(v)))
        else:
            items.append((new_key, v))
    return dict(items)

def process_metadata(flattened_metadata: Dict[str, Any]) -> Dict[str, Any]:
    processed_metadata = {}
    for key, value in flattened_metadata.items():
        if isinstance(value, str):
            try:
                parsed_value = json.loads(value)
                if isinstance(parsed_value, dict):
                    processed_metadata.update(flatten_dict(parsed_value, parent_key=key))
                else:
                    processed_metadata[key] = value
            except json.JSONDecodeError:
                processed_metadata[key] = value
        else:
            processed_metadata[key] = value
    return processed_metadata

def results_to_dataframe(results: Dict[str, Any]) -> pd.DataFrame:
    data = []
    for match in results.get('matches', []):
        row = {
            'Segment ID': match['id'],
            'similarity_score': match['score']
        }
        
        metadata = match.get('metadata', {})
        flattened_metadata = flatten_dict(metadata)
        
        processed_metadata = process_metadata(flattened_metadata)
        
        column_mapping = {
            'Name': 'Segment Name',
            'BrandName': 'Brand Name',
            'raw_string': 'Segment Description',
            'relevance_score': 'Relevance Score',
            'UniqueUserCount': 'Unique User Count',
            'CPMRateInAdvertiserCurrency_Amount': 'CPM Rate'
        }
        
        for old_name, new_name in column_mapping.items():
            if old_name in processed_metadata:
                processed_metadata[new_name] = processed_metadata.pop(old_name)
        
        row.update(processed_metadata)
        data.append(row)
    
    df = pd.DataFrame(data)
    return df

def add_metrics_columns(df: pd.DataFrame, vertical: str) -> pd.DataFrame:
    # Ensure these columns exist in the DataFrame
    required_columns = ['overall_cpa', 'overall_ctr', f'{vertical.lower()}_cpa', f'{vertical.lower()}_ctr']
    for col in required_columns:
        if col not in df.columns:
            print(f"Warning: {col} not found in DataFrame")
            df[col] = None  # or some default value

    # Rename columns to match the desired output
    df['Overall CPA'] = df['overall_cpa']
    df['Overall CTR'] = df['overall_ctr']
    df[f'{vertical} CPA'] = df[f'{vertical.lower()}_cpa']
    df[f'{vertical} CTR'] = df[f'{vertical.lower()}_ctr']
    
    # Convert CPM Rate to float if it's not already
    if 'CPM Rate' in df.columns:
        df['CPM Rate'] = df['CPM Rate'].apply(lambda x: float(x) if isinstance(x, str) else x)
    else:
        print("Warning: CPM Rate column not found")
    
    return df

def calculate_segment_score(df: pd.DataFrame, vertical: str) -> pd.DataFrame:
    df['Segment Score'] = df['Relevance Score'] * df[f'{vertical} Normalized Score'] / 100
    df['Segment Score'] = df['Segment Score'].round(3)
    df['Overall Normalized Score'] = df['Overall Normalized Score'].round(3)
    df[f'{vertical} Normalized Score'] = df[f'{vertical} Normalized Score'].round(3)
    return df

def filter_non_us(df: pd.DataFrame) -> pd.DataFrame:
    # Compile the pattern once
    pattern = re.compile(r'\b(' + '|'.join(map(re.escape, NON_US_LOCATIONS)) + r')\b', re.IGNORECASE)
    
    # Concatenate relevant columns only
    relevant_columns = ['Segment Name', 'Segment Description', 'Brand Name', 'Segment ID']
    df['concatenated'] = df[relevant_columns].astype(str).agg(' '.join, axis=1)
    
    # Use vectorized operations
    mask = ~df['concatenated'].str.contains(pattern, regex=True)
    
    # Apply the mask and drop the temporary column
    filtered_df = df[mask].drop(columns=['concatenated'])
    
    print(f"Filtered out {len(df) - len(filtered_df)} non-US locations")
    
    return filtered_df

def filter_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop_duplicates(subset=['Segment Description', 'Segment Name'], keep='first')

def process_dataframe(df: pd.DataFrame, query: str, vertical: str) -> pd.DataFrame:
    df = filter_non_us(df)
    df = df.sort_values('CPM Rate', ascending=True)
    df = filter_duplicates(df)
    df = add_metrics_columns(df, vertical)
    df = calculate_z_scores(df, vertical)
    df = calculate_normalized_scores(df, vertical)
    return df