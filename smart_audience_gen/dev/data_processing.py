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

def results_to_dataframe(results):
    data = []
    for match in results.get('matches', []):  # Access 'matches' key from results dictionary
        row = {
            'id': match['id'],
            'vector_score': match['score']
        }
        
        # Handle metadata
        metadata = match.get('metadata', {})
        flattened_metadata = flatten_dict(metadata)
        
        # Create a new dictionary to store processed values
        processed_metadata = {}
        
        # Handle potential JSON strings in metadata
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
        
        row.update(processed_metadata)
        data.append(row)
    
    df = pd.DataFrame(data)
    return df
