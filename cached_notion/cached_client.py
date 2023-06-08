from abc import abstractmethod
from datetime import timedelta, datetime
from typing import Optional, Dict, Union, Any

import httpx
from notion_client import Client
from notion_client.client import ClientOptions
from sqlitedict import SqliteDict

from cached_notion.cached_api_endpoints import CachedBlocksEndpoint, CachedPagesEndpoint, CachedDatabasesEndpoint


class NotionCache:
    @abstractmethod
    def get(self, notion_id: str, default=None):
        pass

    @abstractmethod
    def set(self, notion_id: str, value):
        pass

    def is_recently_cached(self, notion_id: str, delta: Optional[Union[timedelta, int]] = None):
        if delta is None:
            delta = timedelta(hours=1)
        elif isinstance(delta, int):
            delta = timedelta(hours=delta)

        obj = self.get(notion_id)
        if obj is None:
            return False

        cached_time = datetime.fromisoformat(
            obj.get("cached_time", "2000-01-01T00:00:00.000000"))

        return datetime.now() - cached_time < delta

    def is_outdated(self, notion_id: str, notion_obj: Optional[Dict]):
        if notion_obj is None:
            return False

        obj = self.get(notion_id)
        if obj is None:
            return True

        last_updated = obj.get("last_edited_time", 0)
        return last_updated != notion_obj.get("last_edited_time", "")

    def get_object_type(self, notion_id: str):
        obj = self.get(notion_id)
        if obj is None:
            return None
        return obj.get("object", "unknown")


class SqliteDictCache(NotionCache):
    def __init__(self, path):
        self.path = path
        self.db = SqliteDict(path, autocommit=True)

    def get(self, notion_id, default=None):
        return self.db.get(notion_id, default)

    def set(self, notion_id, value):
        self.db[notion_id] = value


class CachedClient(Client):
    def __init__(
            self,
            options: Optional[Union[Dict[Any, Any], ClientOptions]] = None,
            client: Optional[httpx.Client] = None,
            cache: Optional[NotionCache] = None,
            cache_delta: Optional[Union[timedelta, int]] = None,
            **kwargs: Any,
    ):
        super().__init__(options, client, **kwargs)
        if cache is None:
            self.cache = SqliteDictCache("notion_cache.sqlite")
        else:
            self.cache = cache

        self.cache_delta = cache_delta
        self.blocks = CachedBlocksEndpoint(self)
        self.pages = CachedPagesEndpoint(self)
        self.databases = CachedDatabasesEndpoint(self)