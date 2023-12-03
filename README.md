# CachedNotion 🔧
**CachedNotion** offers an enhanced, caching-enabled interface for interacting with Notion APIs. While it's a work in progress 🚧, its core functionality is fully operational, ensuring efficient and smooth integration.

## What's New 🌟
- **Critical Caching Issue Resolved:** We've tackled a significant caching problem to ensure more reliable and faster access to your Notion data.
- Stay tuned for ongoing updates and improvements! 💼

## Basic Usage 📖
Effortlessly replace `NotionClient` with `CachedClient` for an optimized experience:
```python
from cached_notion.cached_client import CachedClient

# Initialize CachedClient with your Notion token and desired cache settings
client = CachedClient(auth=os.environ["NOTION_TOKEN"], cache_delta=24)
url = "https://www.notion.so/xxx/xxx"
normalized_url = normalize_url(url)
nid, object_type = get_id_with_object_type(normalized_url)

# Use CachedClient to interact with Notion by providing the Notion ID
page = client.pages.retrieve(nid)
database = client.databases.retrieve(nid)
block = client.blocks.retrieve(nid)
```

## Utility Functions 🛠️
Maximize your productivity with these handy functions:
```python
from cached_notion.utils import normalize_url, get_id_with_object_type, retrieve_object

# Normalize the URL and extract the Notion ID and object type
url = "https://www.notion.so/xxx/xxx"
normalized_url = normalize_url(url)
nid, object_type = get_id_with_object_type(normalized_url)

# Use the retrieve_object utility function to get the object from Notion
obj = retrieve_object(client, nid, object_type)

# Now you can work with the retrieved object
print(obj)
```

```python
from cached_notion.utils import normalize_url, get_id_with_object_type, retrieve_all_content

# Normalize the URL and extract the Notion ID and object type
url = "https://www.notion.so/xxx/xxx"
normalized_url = normalize_url(url)
nid, object_type = get_id_with_object_type(normalized_url)

# Use the retrieve_all_content function to get the full content from Notion
full_content = retrieve_all_content(client, nid, object_type)

# Now you can work with the full content retrieved from Notion
print(full_content)
```

## Enhanced Caching Strategy 💡
- **Cache Delta Explained:** Set `cache_delta` to manage how often the API calls the Notion API. A positive value uses cached content within the specified hours, reducing API calls. A zero value always fetches fresh content but minimizes API usage when used with `retrieve_all_content`.
