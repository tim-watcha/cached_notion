from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional, TYPE_CHECKING

from notion_client.api_endpoints import BlocksEndpoint, Endpoint, PagesEndpoint, DatabasesEndpoint, \
    BlocksChildrenEndpoint
from notion_client.helpers import collect_paginated_api
from notion_client.typing import SyncAsync
from tenacity import retry, wait_exponential, stop_after_attempt

if TYPE_CHECKING:
    from .cached_client import CachedClient


class CachedEndpoint(Endpoint):
    def __init__(self, parent: "CachedClient") -> None:
        super().__init__(parent)


def cached_endpoint(retrieve_func):
    @wraps(retrieve_func)
    @retry(wait=wait_exponential(multiplier=1, min=1, max=128), stop=stop_after_attempt(7))
    def wrapper(self, id: str, cached: Optional[Dict[Any, Any]] = None, **kwargs: Any) -> SyncAsync[Any]:

        self.parent.logger.debug(f"ID: {id}, Cached: {cached}, Kwargs: {kwargs}")
        self.parent.logger.debug(f"Cached: {self.parent.cache.is_recently_cached(id, self.parent.cache_delta)}")
        self.parent.logger.debug(f"Outdated: {self.parent.cache.is_outdated(id, cached)}")
        self.parent.logger.debug(self.parent.cache.get(id))
        if (self.parent.cache.is_recently_cached(id, self.parent.cache_delta) \
            or not self.parent.cache.is_outdated(id, cached)) and cached is not None:
            self.parent.logger.info(f"Cache hit! Retrieving {id}")
            return self.parent.cache.get(id)

        resp = retrieve_func(self, id, **kwargs)

        # Update cache if response is outdated
        if self.parent.cache.is_outdated(id, resp):
            resp["cached_time"] = datetime.now().isoformat()
            resp["children_reached_end"] = False
            self.parent.cache.set(id, resp)

        return resp

    return wrapper


class CachedBlocksEndpoint(BlocksEndpoint, CachedEndpoint):
    parent: "CachedClient"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.children = CachedBlocksChildrenEndpoint(*args, **kwargs)

    @cached_endpoint
    def retrieve(self, block_id: str, **kwargs: Any) -> SyncAsync[Any]:
        return super().retrieve(block_id, **kwargs)


class CachedPagesEndpoint(PagesEndpoint, CachedEndpoint):
    parent: "CachedClient"

    @cached_endpoint
    def retrieve(self, page_id: str, **kwargs: Any) -> SyncAsync[Any]:
        return super().retrieve(page_id, **kwargs)


class CachedDatabasesEndpoint(DatabasesEndpoint, CachedEndpoint):
    parent: "CachedClient"

    @cached_endpoint
    def retrieve(self, database_id: str, **kwargs: Any) -> SyncAsync[Any]:
        return super().retrieve(database_id, **kwargs)

    def query_all(self, database_id: str, **kwargs: Any) -> SyncAsync[Any]:
        # Retrieve the database from the cache if it exists
        database_cache = self.parent.cache.get(database_id, None)

        # Use cache only when 'entries_completed' is True
        if database_cache and database_cache.get("entries_completed", False):
            entries = database_cache.get("entries", [])
            self.parent.logger.info(f"Cache hit! Querying {database_id}")
            return entries

        try:
            resp = collect_paginated_api(self.query, database_id=database_id, **kwargs)
        except Exception as e:
            self.parent.logger.error(e)
            self.parent.logger.error(database_id, kwargs)
            return []
        self.parent.logger.debug(resp)

        # If the database is not cached, don't cache the entries
        # TODO: Add a flag to caching parent first so that we can cache the entries
        if database_cache:
            entries = resp

            database_cache["entries"] = entries
            database_cache["entries_completed"] = True

            self.parent.cache.set(database_id, database_cache)

            for entry in resp:
                # if entry is outdated, update cache
                if self.parent.cache.is_outdated(entry["id"], entry):
                    self.parent.cache.set(entry["id"], entry)

        return resp


class CachedBlocksChildrenEndpoint(BlocksChildrenEndpoint, CachedEndpoint):
    parent: "CachedClient"

    def list_all(self, block_id: str, **kwargs: Any) -> \
            SyncAsync[Any]:
        # Retrieve the block from the cache if it exists
        block_cache = self.parent.cache.get(block_id, None)

        # Use cache only when 'children_completed' is True
        if block_cache and block_cache.get("children_completed", False):
            children = block_cache.get("children", [])
            self.parent.logger.info(f"Cache hit! Listing {block_id}")
            return children

        try:
            resp = collect_paginated_api(self.list, block_id=block_id, **kwargs)
        except Exception as e:
            self.parent.logger.error(e)
            self.parent.logger.error(block_id, kwargs)
            return []
        self.parent.logger.debug(resp)

        # If the parent block is not cached, don't cache the children
        # TODO: Add a flag to caching parent first so that we can cache the children
        if block_cache:
            children = resp

            block_cache["children"] = children
            block_cache["children_completed"] = True

            self.parent.cache.set(block_id, block_cache)

            for block in resp:
                # if block is outdated, update cache
                if self.parent.cache.is_outdated(block["id"], block):
                    self.parent.cache.set(block["id"], block)

        return resp
