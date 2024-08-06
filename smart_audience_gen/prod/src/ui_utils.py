import json
from deepdiff import DeepDiff

def extract_description(item):
    if isinstance(item, dict) and 'description' in item:
        return item['description']
    elif isinstance(item, str):
        return item
    elif isinstance(item, list):
        return [extract_description(subitem) for subitem in item]
    else:
        return str(item)  # fallback for unexpected types

def get_json_diff(old_json, new_json):

    diff = DeepDiff(old_json, new_json, verbose_level=2)
    
    changes = {
        "added": [],
        "removed": []
    }
    
    for key, value in diff.items():
        if key in ["dictionary_item_added", "iterable_item_added"]:
            for path, item in value.items():
                changes["added"].extend(extract_description(item))
        
        elif key in ["dictionary_item_removed", "iterable_item_removed"]:
            for path, item in value.items():
                changes["removed"].extend(extract_description(item))

    return changes