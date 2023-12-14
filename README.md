# CachedNotion 🔧
**CachedNotion** offers an enhanced, caching-enabled interface for interacting with Notion APIs. While it's a work in progress 🚧, its core functionality is fully operational, ensuring efficient and smooth integration.

## What's New 🌟
- **Critical Caching Issue Resolved:** We've tackled a significant caching problem to ensure more reliable and faster access to your Notion data.
- Stay tuned for ongoing updates and improvements! 💼

## Installation 📦

**CachedNotion** is currently available on TestPyPI. You can install it using either pip or Poetry.

### Using pip

To install `CachedNotion` using pip, run the following command:

```bash
pip install cached-notion
```

### Using Poetry

For those using Poetry, you can add `CachedNotion` to your project as follows:

```bash
poetry add cached-notion
```

---

## New Feature: Notion to Markdown Conversion 📝

**CachedNotion** now offers an innovative feature to convert Notion pages into Markdown format. This is invaluable for users wanting to document, backup, or share their Notion content in a standardized format.

### Function Overview

- `url_to_md`: Converts a Notion URL into a Markdown string. It handles nested content up to a specified depth, making it perfect for diverse documentation needs.
- `id_to_md`: A complementary function to `url_to_md`, handling individual IDs and managing content depth.

### Understanding Parameters

- `max_depth`: This parameter in `url_to_md` specifies the recursive depth for crawling through the Notion content. A value of `-1` indicates no limit, ensuring a comprehensive conversion that includes all nested elements. Adjust this parameter to control how deep the function traverses through nested pages or blocks.
- `subs`: Short for "sub-items," this parameter represents the remaining sub-items that are yet to be processed for further depths. It's crucial for managing and tracking the conversion process across nested levels of content.

### Using `url_to_md`

Quickly convert any Notion page into Markdown:
```python
from cached_notion.utils import url_to_md

# Initialize CachedClient
client = CachedClient(auth=os.environ["NOTION_TOKEN"], cache_delta=24)

# Convert a Notion URL to Markdown, specifying the depth of content to include
notion_url = "https://www.notion.so/xxx/xxx"
markdown_string, remaining_subs = url_to_md(client, notion_url, max_depth=-1)

# Markdown string is now ready, along with any remaining sub-items for further processing
print(markdown_string)
```

This function is especially useful for thorough documentation, platform exports, or content backups.

### Using `id_to_md`

`id_to_md` can also be used independently for tailored Markdown generation processes, providing flexibility and control over the depth and content of the conversion.

---
## Basic Usage 📖
Effortlessly replace `NotionClient` with `CachedClient` for an optimized experience:
```python
from cached_notion.cached_client import CachedClient
from cached_notion.utils import normalize_url, get_id_with_object_type
import os

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
from cached_notion.cached_client import CachedClient
from cached_notion.utils import normalize_url, get_id_with_object_type, retrieve_object
import os

client = CachedClient(auth=os.environ["NOTION_TOKEN"], cache_delta=24)

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
from cached_notion.cached_client import CachedClient
from cached_notion.utils import normalize_url, get_id_with_object_type, retrieve_all_content
import os
client = CachedClient(auth=os.environ["NOTION_TOKEN"], cache_delta=24)

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
