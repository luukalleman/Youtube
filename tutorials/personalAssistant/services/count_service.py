import requests
from config.settings import NOTION_API_KEY


def delete_specific_callout_blocks(page_id: str):
    notion_api_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

    # Fetch all blocks in the page
    response = requests.get(notion_api_url, headers=headers)
    
    if response.status_code != 200:
        print(f"Failed to retrieve blocks: {response.text}")
        return
    
    blocks = response.json().get('results', [])

    # Delete each callout block that matches the specified texts
    for block in blocks:
        if block['type'] == 'callout':
            # block_text = block['callout']['rich_text'][0]['text']['content']
            # if block_text in callout_texts:
            delete_block_url = f"https://api.notion.com/v1/blocks/{block['id']}"
            delete_response = requests.delete(delete_block_url, headers=headers)
            
            if delete_response.status_code != 200:
                print(f"Failed to delete block {block['id']}: {delete_response.text}")


def update_callout_with_count(database_id: str, page_id: str, title: str, emoji: str):
    notion_api_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # Ensure you use the correct API version
    }

    # Fetch the number of rows in the database
    response = requests.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",  # Correct URL
        headers=headers,
        json={}  # The empty JSON will query all rows
    )
    
    if response.status_code != 200:
        print(f"Failed to query the database: {response.text}")
        return
    
    data = response.json()
    row_count = len(data.get('results', []))

    # Create the rich_text object with the count
    rich_text_content = {
        "object": "block",
        "type": "callout",
        "callout": {
            "rich_text": [
                {
                    "type": "text",
                    "text": {
                        "content": f"{title}: {row_count}"
                    }
                }
            ],
            "icon": {
                "type": "emoji",
                "emoji": emoji
            },
            "color": "default"
        }
    }

    # Update the callout block in Notion
    update_response = requests.patch(notion_api_url, headers=headers, json={"children": [rich_text_content]})
    
    if update_response.status_code != 200:
        print(f"Failed to update callout block in Notion: {update_response.text}")


def update_callout_with_post(database_id: str, page_id: str):
    notion_api_url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"  # Ensure you use the correct API version
    }

    # Fetch the rows in the database
    response = requests.post(
        f"https://api.notion.com/v1/databases/{database_id}/query",  # Correct URL
        headers=headers,
        json={}  # The empty JSON will query all rows
    )
    
    if response.status_code != 200:
        print(f"Failed to query the database: {response.text}")
        return
    
    data = response.json()
    row_count = len(data.get('results', []))

    if row_count > 0:
        # Loop through the rows and extract the content
        for row in data.get('results', []):
            content_text = row.get('properties', {}).get('Content', {}).get('rich_text', [{}])[0].get('text', {}).get('content', '')
            if content_text:
                # Create the callout block for the content
                callout_content = {
                    "object": "block",
                    "type": "callout",
                    "callout": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": content_text
                                }
                            }
                        ],
                        "icon": {
                            "type": "emoji",
                            "emoji": "✍️"  # Example emoji, can be customized
                        },
                        "color": "default"
                    }
                }

                # Update the callout block in Notion
                update_response = requests.patch(notion_api_url, headers=headers, json={"children": [callout_content]})
                
                if update_response.status_code != 200:
                    print(f"Failed to update callout block in Notion: {update_response.text}")
                else:
                    print(f"Successfully added content callout to the page.")
    else:
        print("No content found in the Generated Content database.")