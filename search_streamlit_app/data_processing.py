import pandas as pd
import json
from typing import Dict, Any

def flatten_dict(d, parent_key='', sep='_'):
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

def process_metadata(flattened_metadata):
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

def results_to_dataframe(results):
    data = []
    for match in results.get('matches', []):
        row = {
            'Segment ID': match['id'],
            'similarity_score': match['score']
        }
        
        metadata = match.get('metadata', {})
        flattened_metadata = flatten_dict(metadata)
        
        processed_metadata = process_metadata(flattened_metadata)
        
        # Rename specific columns for better readability
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
