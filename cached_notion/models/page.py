from pprint import pprint
from typing import List, Dict

from pydantic import BaseModel

from cached_notion.models.blocks import Block
from cached_notion.models.property import PropertyType, TitleProperty


class Page(BaseModel):
    properties: Dict[str, PropertyType]
    children: List[Block]
    url: str
    id: str
    parent: Dict
    last_edited_time: str
    created_time: str

    def to_md(self):
        pprint(self.properties)
        res = ""
        # get TitleProperty first
        titles = filter(lambda v: type(v) is TitleProperty, self.properties.values())
        for v in titles:
            res += f"# {v.to_md()}\n\n"

        # get PropertiesModel
        for k, v in self.properties.items():
            if type(v) is not TitleProperty:
                res += f"{k}: {v.to_md()}\n\n"

        for child in self.children:
            res += child.to_md(0)
        return res
