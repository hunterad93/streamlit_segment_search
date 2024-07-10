import pandas as pd
import json
import re
from typing import Dict, Any

def extract_and_correct_json(text):
    # Try to find JSON content enclosed in triple backticks first
    json_pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'
    json_match = re.search(json_pattern, text)
    
    if json_match:
        json_string = json_match.group(1)
    else:
        # If no triple backticks, try to extract JSON using curly braces
        json_pattern = r'\{[\s\S]*\}'
        json_match = re.search(json_pattern, text)
        if json_match:
            json_string = json_match.group(0)
        else:
            print("No JSON found in the text")
            return None
    
    # Advanced corrections
    json_string = re.sub(r',\s*}', '}', json_string)  # Remove trailing commas in objects
    json_string = re.sub(r',\s*]', ']', json_string)  # Remove trailing commas in arrays
    json_string = re.sub(r'}\s*{', '},{', json_string)  # Add commas between objects
    json_string = re.sub(r']\s*\[', '],[', json_string)  # Add commas between arrays
    json_string = re.sub(r'"\s*:\s*"', '": "', json_string)  # Normalize spacing around colons
    json_string = re.sub(r'"\s*,\s*"', '", "', json_string)  # Normalize spacing around commas
    
    # Balance brackets and braces
    open_braces = json_string.count('{')
    close_braces = json_string.count('}')
    open_brackets = json_string.count('[')
    close_brackets = json_string.count(']')
    
    json_string += '}' * (open_braces - close_braces)
    json_string += ']' * (open_brackets - close_brackets)
    
    try:
        return json_string
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
        print("JSON string after corrections:")
        print(json_string)
        return None

def extract_included_json(json_string: str) -> str:
    try:
        # Parse the JSON string
        data: Dict[str, Any] = json.loads(json_string)
        
        # Extract the "included" object
        included: Dict[str, Any] = data.get("Audience", {}).get("included", {})
        
        # Return the "included" object as a JSON string
        return json.dumps(included, indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON string"
    except AttributeError:
        return "Error: Unexpected JSON structure"
    
def extract_excluded_json(json_string: str) -> str:
    try:
        # Parse the JSON string
        data: Dict[str, Any] = json.loads(json_string)
        
        # Extract the "excluded" object
        excluded: Dict[str, Any] = data.get("Audience", {}).get("excluded", {})
        
        # Return the "excluded" object as a JSON string
        return json.dumps(excluded, indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON string"
    except AttributeError:
        return "Error: Unexpected JSON structure"
    
def recombine_json(included_json: str, excluded_json: str) -> str:
    try:
        included_data: Dict[str, Any] = json.loads(included_json)
        excluded_data: Dict[str, Any] = json.loads(excluded_json)
        
        recombined_data: Dict[str, Any] = {
            "Audience": {
                "included": included_data,
                "excluded": excluded_data
            }
        }
        
        return json.dumps(recombined_data, indent=2)
    except json.JSONDecodeError:
        return "Error: Invalid JSON string in either included or excluded data"


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

def select_context(history, num_first=2, num_recent=7):
    if len(history) <= num_first + num_recent:
        return history
    print('history length' + str(len(history)))
    return history[:num_first] + history[-(num_recent):]