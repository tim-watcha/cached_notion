import logging
import os
from collections import defaultdict
from pprint import pprint
from typing import List
from typing import Tuple, Union, Optional, Dict
from urllib.parse import urlparse, parse_qs
from uuid import UUID

import tqdm
from notion_client import Client

from cached_notion.cached_client import CachedClient
from cached_notion.models.property import PropertiesModel
from cached_notion.pretty_logger import setup_logger


def normalize_url(url: str) -> str:
    url = url.strip()
    parsed_url = urlparse(url)
    query_parameters = parse_qs(parsed_url.query)

    if "p" in query_parameters:
        page_id = query_parameters["p"][0]
        new_url = f"{parsed_url.scheme}://{parsed_url.netloc}/{page_id}"
        return new_url
    return url


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
    client.logger.debug(f"Retrieved object: {notion_id} {object_type}")
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


def retrieve_page(
        client: Union[Client, CachedClient],
        notion_id: str,
        object_type: str = "unknown",
        given_block: Optional[Dict] = None):
    notion_obj = retrieve_object(client, notion_id, object_type, given_block)
    client.logger.debug(f"Retrieved object: {notion_id} {object_type}")
    if notion_obj.get("has_children", False) or notion_obj.get("object", "") == "page":
        notion_obj["children"] = client.blocks.children.list_all(notion_id)
        for child in notion_obj["children"]:
            if child['type'] != 'child_page':
                content = retrieve_page(client, child["id"], child["type"], child)
                child.update(content)
    if notion_obj["object"] == "database" or notion_obj["object"] == "block" and notion_obj["type"] == "child_database":
        entries = client.databases.query_all(notion_id)
        notion_obj["entries"] = entries
    return notion_obj


def _get_page_info(d):
    res = dict()
    try:
        properties = PropertiesModel.parse_properties(d.get('properties', {}))
    except Exception as e:
        print(e)
        print(d.get('properties', {}))
        raise e

    res["title"] = properties.get_title_md()
    res["properties"] = properties.get_property_md()
    res["url"] = d.get("url", "")
    res["id"] = d["id"]
    res["parent"] = d["parent"].get('block_id', None)
    return res


def _get_page(notion_client, d):
    res = _get_page_info(d)
    res['content'] = ""
    subs = []
    for c in d.get('children', []):
        r, s = _convert_block(notion_client, c, [], 0)
        res["content"] += r
        subs += s
    return res, subs


def _rich_text_to_md(rich_text_list):
    md_text = []
    for text_item in rich_text_list:
        plain_text = text_item["plain_text"]
        annotations = text_item["annotations"]

        if annotations["bold"]:
            plain_text = f"**{plain_text}**"
        if annotations["italic"]:
            plain_text = f"*{plain_text}*"
        if annotations["strikethrough"]:
            plain_text = f"~~{plain_text}~~"
        if annotations["underline"]:
            plain_text = f"__{plain_text}__"
        if annotations["code"]:
            plain_text = f"`{plain_text}`"
        if text_item["href"]:
            plain_text = f"[{plain_text}]({text_item['href']})"
        md_text.append(plain_text)

    return "".join(md_text)


_numbered: defaultdict = defaultdict(int)


def _code_block_to_md(block):
    code_block = block["code"]
    language = code_block["language"]
    code_text = _rich_text_to_md(code_block["rich_text"])
    return f"```{language}\n{code_text}\n```\n"


def _table_to_md(block):
    table_width = block["table"]["table_width"]
    has_column_header = block["table"]["has_column_header"]
    has_row_header = block["table"]["has_row_header"]

    # Retrieve table rows
    table_rows = block["children"]

    table_md = []
    for row_idx, row_block in enumerate(table_rows):
        if row_block["type"] != "table_row":
            print(
                f"Unexpected block type inside table: {row_block['type']}"
            )
            continue

        row_cells = row_block["table_row"]["cells"]
        if len(row_cells) != table_width:
            print(
                "Number of cells in the row does not match the table width."
            )
            continue

        row_cells_md = []
        for cell_idx, cell in enumerate(row_cells):
            cell_md = _rich_text_to_md(cell)
            if has_column_header and row_idx == 0:
                cell_md = f"**{cell_md}**"
            if has_row_header and cell_idx == 0:
                cell_md = f"**{cell_md}**"
            row_cells_md.append(cell_md)

        table_md.append("| " + " | ".join(row_cells_md) + " |")

    # Add table header row separator
    if has_column_header:
        table_md.insert(1, "| " + " | ".join(["---"] * table_width) + " |")
    block["children"] = None
    return "\n".join(table_md)


def _convert_block(notion_client, block: Dict, subs: List[Dict[str, str]], depth: int):
    block_type = block["object"]
    if block_type == "block":
        block_type = block["type"]

    res = " " * depth
    if block_type == "database":
        block_type = "child_database"

    if block_type == "paragraph":
        res += _rich_text_to_md(block["paragraph"]["rich_text"]) + "\n"
    elif block_type == "callout":
        res += f"> {_rich_text_to_md(block['callout']['rich_text'])}\n"
    elif block_type == "child_page":
        res += f"[{block['child_page']['title']}]({block['id']})\n"
        subs += [{"type": "child_page", "id": block["id"]}]
    elif block_type == "child_database":
        res += f"[{block['child_database']['title']}]({block['id']})\n"
        res += _convert_entries(block['entries'])
        subs += [{'type': 'page', 'id': entry['id']} for entry in block['entries']]
    elif block_type == "heading_1":
        res += f"# {_rich_text_to_md(block['heading_1']['rich_text'])}\n"
    elif block_type == "heading_2":
        res += f"## {_rich_text_to_md(block['heading_2']['rich_text'])}\n"
    elif block_type == "heading_3":
        res += f"### {_rich_text_to_md(block['heading_3']['rich_text'])}\n"
    elif block_type == "divider":
        res += "---\n"
    elif block_type == "toggle":
        res += f"> {_rich_text_to_md(block['toggle']['rich_text'])}\n"
    elif block_type == "numbered_list_item":
        _numbered[depth] += 1
        res += f"{_numbered[depth]}. {_rich_text_to_md(block['numbered_list_item']['rich_text'])}\n"
    elif block_type == "bulleted_list_item":
        res += f"* {_rich_text_to_md(block['bulleted_list_item']['rich_text'])}\n"
    elif block_type == "link_to_page":
        d = _get_page_info(retrieve_object(notion_client, block["link_to_page"]["page_id"]))
        res += f"[{d['title']}]({d['id']})\n"
    elif block_type == "code":
        res += _code_block_to_md(block)
    elif block_type == "quote":
        res += f"> {_rich_text_to_md(block['quote']['rich_text'])}\n"
    elif block_type == "bookmark":
        res += f"[{block['bookmark']['caption']}]({block['bookmark']['url']})\n"
    elif block_type == "table":
        res += _table_to_md(block)
    elif block_type == "to_do":
        checked = block["to_do"]["checked"]
        text = _rich_text_to_md(block["to_do"]["rich_text"])
        res += f"{'[v]' if checked else '[ ]'} {text}\n"

    else:
        _numbered[depth] = 0
        if block_type not in {"column_list", "column", "image", "unsupported", "synced_block", "table_of_contents",
                              "file", "audio", "video", "link_preview", "embed"}:
            print(">>>>>>>>>>>>", block_type, block['id'])
            print(block)
    for column in (block.get("children", []) or []):
        r, s = _convert_block(notion_client, column, subs, depth + 1)
        res += r
        subs = s
    return res, subs


def _convert_entries(entries):
    res = []
    for entry in entries:
        properties = entry["properties"]
        res += [PropertiesModel.parse_properties(properties).to_md()]

    res = "\n".join(res)
    return res


# notion
def _traverse(notion_client, d, depth=0):
    global _numbered
    _numbered = defaultdict(int)
    res = []
    subs = []
    if d.get("object", "") == "page":
        r, s = _get_page(notion_client, d)
        res += [r]
        subs += s
    elif d.get("object", "") == "database":
        r, s = _get_page(notion_client, d)
        res += [r]
        subs += s
    for k, v in d.items():
        if isinstance(v, dict):
            r, s = _traverse(notion_client, v, depth + 1)
            res += r
            subs += s
        elif isinstance(v, list):
            for i in v:
                r, s = _traverse(notion_client, i, depth + 1)
                res += r
                subs += s
    return res, subs


def url_to_md(notion_client, notion_url: str, max_depth: int = -1) -> Tuple[str, List[Dict[str, str]]]:
    """Convert a Notion URL to a markdown string.
    max_depth: -1 means no limit"""

    notion_url = normalize_url(notion_url)

    notion_id, object_type = get_id_with_object_type(notion_url)
    subs = [{'type': object_type, 'id': notion_id}]
    res = []

    res, subs = id_to_md(notion_client, res, subs, max_depth)

    res2 = list(filter(lambda x: len(x.get('content', '').strip()) > 0, res))
    mds = "\n\n".join([f"""\
    ---
    [{r['title']}]({r['url']})

    {r['properties']}

    parent: {r['parent']}

    id: {r['id']}

    content:
    {r['content']}
    ---""" for r in res2])
    return mds, subs


def id_to_md(notion_client, res, subs, max_depth, cur_depth=0):
    new_subs = []
    for sub in tqdm.tqdm(subs):
        notion_id = sub["id"]
        object_type = sub["type"]
        content = retrieve_page(notion_client, notion_id, object_type)
        r, s = _traverse(notion_client, content)
        res += r
        new_subs += s
    if cur_depth < max_depth or max_depth == -1:
        res, new_subs = id_to_md(notion_client, res, new_subs, max_depth, cur_depth + 1)
    return res, new_subs


def _main():
    logger = setup_logger(__name__)
    notion_client = CachedClient(
        auth=os.environ["NOTION_TOKEN"],
        logger=logger,
        log_level=logging.ERROR,
        cache_delta=24,
    )

    res, subs = url_to_md(notion_client, "https://www.notion.so/watcha/XXX", 1)
    print(res)
    pprint(subs)


if __name__ == '__main__':
    _main()
