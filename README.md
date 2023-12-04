# CachedNotion 🔧
**CachedNotion** offers an enhanced, caching-enabled interface for interacting with Notion APIs. While it's a work in progress 🚧, its core functionality is fully operational, ensuring efficient and smooth integration.

## What's New 🌟
- **Critical Caching Issue Resolved:** We've tackled a significant caching problem to ensure more reliable and faster access to your Notion data.
- Stay tuned for ongoing updates and improvements! 💼

## Installation 📦

**CachedNotion** is currently available on TestPyPI. You can install it using either pip or Poetry.

### Using pip

To install `CachedNotion` from TestPyPI using pip, run the following command:

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple cached-notion
```

This command tells pip to look for the package in TestPyPI but also checks the official PyPI for any dependencies that are not available in TestPyPI.

### Using Poetry

For those using Poetry, you can add `CachedNotion` to your project from TestPyPI as follows:

1. Add TestPyPI as a secondary repository to your `pyproject.toml`:

   ```toml
   [[tool.poetry.source]]
   name = "testpypi"
   url = "https://test.pypi.org/simple/"
   secondary = true
   ```

2. Add `cached-notion` to your project dependencies:

   ```bash
   poetry add cached-notion --source testpypi
   ```

Poetry will handle the resolution of dependencies from both TestPyPI and the official PyPI repository.


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
