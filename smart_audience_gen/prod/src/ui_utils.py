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
    if isinstance(old_json, str):
        old_json = json.loads(old_json)
    if isinstance(new_json, str):
        new_json = json.loads(new_json)

    diff = DeepDiff(old_json, new_json, verbose_level=2)
    
    changes = {
        "added": [],
        "removed": [],
        "changed": []
    }
    
    for key, value in diff.items():
        if key == "values_changed":
            for path, change in value.items():
                if "description" in path:
                    category = path.split("']['")[1]
                    old_value = extract_description(change['old_value'])
                    new_value = extract_description(change['new_value'])
                    changes["changed"].append(f"{old_value} -> {new_value}")
        
        elif key in ["dictionary_item_added", "iterable_item_added"]:
            for path, item in value.items():
                description = extract_description(item)
                if isinstance(description, list):
                    changes["added"].extend(description)
                else:
                    changes["added"].append(description)
        
        elif key in ["dictionary_item_removed", "iterable_item_removed"]:
            for path, item in value.items():
                description = extract_description(item)
                if isinstance(description, list):
                    changes["removed"].extend(description)
                else:
                    changes["removed"].append(description)

    return changes