# CachedNotion 🔧
**CachedNotion** offers an enhanced, caching-enabled interface for interacting with Notion APIs. While it's a work in progress 🚧, its core functionality is fully operational, ensuring efficient and smooth integration.

## What's New 🌟
- **Critical Caching Issue Resolved:** We've tackled a significant caching problem to ensure more reliable and faster access to your Notion data.
- Stay tuned for ongoing updates and improvements! 💼

## Basic Usage 📖
Effortlessly replace `NotionClient` with `CachedClient` for an optimized experience:
```python
from cached_notion.cached_client import CachedClient

# Initialize CachedClient
client = CachedClient(auth=os.environ["NOTION_TOKEN"], cache_delta=24)

# Use CachedClient to interact with Notion
page = client.pages.retrieve("https://www.notion.so/xxx/xxx")
database = client.databases.retrieve("https://www.notion.so/xxx/xxx")
block = client.blocks.retrieve("https://www.notion.so/xxx/xxx")
```

## Utility Functions 🛠️
Maximize your productivity with these handy functions:
```python
from cached_notion.utils import retrieve_all_content

# Retrieve and print all content from a page or database
page = retrieve_all_content(client, notion_id, "page")  # Options: "page", "database", "block", "unknown"
print(page)
print(page.get("children", []))

database = retrieve_all_content(client, notion_id, "database")
print(database)
print(database.get("entries", []))  # Note: This is not an official structure
```

## Enhanced Caching Strategy 💡
- **Cache Delta Explained:** Set `cache_delta` to manage how often the API calls the Notion API. A positive value uses cached content within the specified hours, reducing API calls. A zero value always fetches fresh content but minimizes API usage when used with `retrieve_all_content`.
