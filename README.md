# CachedNotion 🔧
Please note that this project is still under construction 🚧, but basic functions are operational and can be used. 

# Basic Usage 🌟
With our `CachedClient` class, you can simply replace the usual `NotionClient` class for a smoother experience. Here's how to do it:
```python
from cached_notion.cached_client import CachedClient

# Instantiate the CachedClient
client = CachedClient(auth=os.environ["NOTION_TOKEN"], cache_delta=24)

# Retrieve a page
page = client.pages.retrieve("https://www.notion.so/xxx/xxx")

# Retrieve a database
database = client.databases.retrieve("https://www.notion.so/xxx/xxx")

# Retrieve a block
block = client.blocks.retrieve("https://www.notion.so/xxx/xxx")
```

## Utility Functions 🛠️

```python
from cached_notion.utils

# These utility functions recursively retrieve all content from a page or database.
page = retrieve_all_content(client, notion_id, "page")  # Or "database", "block", "unknown" (default)
print(page)
print(page.get("children", []))

database = retrieve_all_content(client, notion_id, "database")
print(database)
print(database.get("entries", []))  # Please note, this is not an official structure
```

# Caching Strategy 💡

## Cache Delta

- When `cache_delta > 0`, and if the content is cached within `cache_delta` hours, the API doesn't call Notion API and returns the cached content instead.

- If `cache_delta = 0`, the API will retrieve the requested content. However, when called by `retrieve_all_content`, the API will only be triggered if the last updated time is outdated. This ensures minimal API usage. 

Stay tuned for more updates! 💼