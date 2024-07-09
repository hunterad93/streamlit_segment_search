import json
import requests
from typing import Dict, Any, List

def load_audience_data(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        return json.load(f)

def create_data_group(advertiser_id: str, group_name: str, segment_ids: List[str], api_key: str) -> str:
    url = 'https://api.thetradedesk.com/v3/thirdparty/datagroup'
    headers = {
        'Content-Type': 'application/json',
        'TTD-Auth': api_key
    }
    payload = {
        'AdvertiserId': advertiser_id,
        'DataGroupName': group_name,
        'ThirdPartyDataIds': segment_ids,
        'SkipUnauthorizedThirdPartyData': True
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Successfully created data group: {group_name}")
        return response.json()['DataGroupId']
    else:
        print(f"Failed to create data group: {group_name}. Error: {response.text}")
        return None

def prepare_data_groups(audience_data: Dict[str, Any], advertiser_id: str, api_key: str) -> Dict[str, List[str]]:
    data_group_ids = {'included': [], 'excluded': []}
    
    for group_type in ['included', 'excluded']:
        if group_type in audience_data['Audience']:
            for category, subcategories in audience_data['Audience'][group_type].items():
                for subcategory in subcategories:
                    segment_ids = [f"{segment['id']}" for segment in subcategory.get('top_k_segments', [])]
                    if segment_ids:
                        group_name = f"{group_type.capitalize()} - {category} - {subcategory['description']}"
                        group_id = create_data_group(advertiser_id, group_name, segment_ids, api_key)
                        if group_id:
                            data_group_ids[group_type].append(group_id)
    
    return data_group_ids

def create_audience(advertiser_id: str, audience_name: str, included_groups: List[str], excluded_groups: List[str], api_key: str) -> None:
    url = 'https://api.thetradedesk.com/v3/thirdparty/audience'
    headers = {
        'Content-Type': 'application/json',
        'TTD-Auth': api_key
    }
    payload = {
        'AdvertiserId': advertiser_id,
        'AudienceName': audience_name,
        'IncludedDataGroupIds': included_groups,
        'ExcludedDataGroupIds': excluded_groups
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        print(f"Successfully created audience: {audience_name}")
    else:
        print(f"Failed to create audience. Error: {response.text}")

def main():
    file_path = 'smart_audience_gen/dev/processed_audience_segments.json'
    api_key = 'YOUR_TTD_API_KEY'
    advertiser_id = 'YOUR_ADVERTISER_ID'
    audience_name = 'My Custom Audience'
    
    audience_data = load_audience_data(file_path)
    data_group_ids = prepare_data_groups(audience_data, advertiser_id, api_key)
    create_audience(advertiser_id, audience_name, data_group_ids['included'], data_group_ids['excluded'], api_key)

if __name__ == '__main__':
    main()