import json
from deepdiff import DeepDiff

def extract_description(item):
    if isinstance(item, dict) and 'description' in item:
        return item['description']
    elif isinstance(item, list):
        return [extract_description(subitem) for subitem in item]
    return str(item)

def get_json_diff(old_json, new_json):
    if isinstance(old_json, str):
        old_json = json.loads(old_json)
    if isinstance(new_json, str):
        new_json = json.loads(new_json)

    diff = DeepDiff(old_json, new_json, verbose_level=2)
    
    changes = {
        "added": [],
        "removed": []
    }
    
    for change_type in ["added", "removed"]:
        for item in diff.get(f"dictionary_item_{change_type}", {}).values():
            description = extract_description(item)
            if isinstance(description, list):
                changes[change_type].extend(description)
            else:
                changes[change_type].append(description)

    return changes