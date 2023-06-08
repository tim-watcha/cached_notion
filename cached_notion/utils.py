from typing import Tuple, Union, Optional, Dict
from urllib.parse import urlparse, parse_qs
from uuid import UUID

from notion_client import Client

from cached_notion.cached_client import CachedClient


def get_id_with_object_type(url: str) -> Tuple[str, str]:
    """Return the ID of a Notion URL."""

    url = url.strip()
    parsed_url = urlparse(url)
    query_parameters = parse_qs(parsed_url.query)

    url_type = "unknown"  # "unknown", "page", "database", "block"
    notion_id = ""

    if parsed_url.fragment != "":
        """If there is a fragment, then it's a block ID"""
        notion_id = parsed_url.fragment
        url_type = "block"
    elif "p" in query_parameters:
        """If p in the query parameters, then it's a front page ID"""
        notion_id = query_parameters["p"][0]
        url_type = "page"
    elif "v" in query_parameters:
        """If v in the query parameters, then it's a database view ID, which means base path is a database"""
        notion_id = parsed_url.path.split("/")[-1]
        url_type = "database"
    elif "-" in parsed_url.path:
        """If there is a hyphen in the path, then it's a page ID"""
        notion_id = parsed_url.path.split("-")[-1]
        url_type = "page"

    if notion_id == "":
        notion_id = parsed_url.path.split("/")[-1]

    notion_id = str(UUID(notion_id))

    return notion_id, url_type


def retrieve_object(
        client: Union[Client, CachedClient],
        notion_id: str,
        object_type: str = "unknown",
        given_block: Optional[Dict] = None):
    if object_type == "unknown" and isinstance(client, CachedClient):
        # get type if object is cached
        object_type = client.cache.get_object_type(notion_id)
    if object_type == "unknown" and given_block is not None:
        # get type if object is given
        object_type = given_block["type"]

    if object_type == "page":
        return client.pages.retrieve(notion_id, cached=given_block)
    elif object_type == "database":
        return client.databases.retrieve(notion_id, cached=given_block)
    elif object_type == "block":
        return client.blocks.retrieve(notion_id, cached=given_block)
    else:
        # TODO: Handle this better
        try:
            return client.pages.retrieve(notion_id, cached=given_block)
        except:
            pass
        try:
            return client.databases.retrieve(notion_id, cached=given_block)
        except:
            pass
        try:
            return client.blocks.retrieve(notion_id, cached=given_block)
        except:
            pass
        raise Exception(f"Could not retrieve object with ID {notion_id}")


def retrieve_all_content(
        client: Union[Client, CachedClient],
        notion_id: str,
        object_type: str = "unknown",
        given_block: Optional[Dict] = None):
    notion_obj = retrieve_object(client, notion_id, object_type, given_block)
    client.logger.pretty(notion_id=notion_id, object_type=object_type, page=notion_obj)

    if notion_obj.get("has_children", False) or notion_obj.get("object", "") == "page":
        notion_obj["children"] = client.blocks.children.list_all(notion_id)
        for child in notion_obj["children"]:
            content = retrieve_all_content(client, child["id"], child["type"], child)
            child.update(content)
    if notion_obj["object"] == "database" or notion_obj["object"] == "block" and notion_obj["type"] == "child_database":
        entries = client.databases.query_all(notion_id)
        notion_obj["entries"] = entries
        for entry in entries:
            content = retrieve_all_content(client, entry["id"], "page")
            entry.update(content)
    return notion_obj
