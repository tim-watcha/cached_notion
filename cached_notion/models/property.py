import uuid
from copy import deepcopy
from datetime import datetime
from typing import List, Dict, Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel, UUID4


class EmojiModel(BaseModel):
    type: Literal['emoji']
    emoji: str


class DatabaseIDModel(BaseModel):
    type: Literal['database_id']
    database_id: uuid.UUID


class TextContent(BaseModel):
    content: str
    link: Optional[Union[str, Dict]] = None


class Annotations(BaseModel):
    bold: bool
    italic: bool
    strikethrough: bool
    underline: bool
    code: bool
    color: str


class RichTextItem(BaseModel):
    type: Literal['text', 'rich_text']
    text: TextContent
    annotations: Annotations
    plain_text: str
    href: Optional[str] = None

    def to_md(self) -> str:
        """Convert a single RichTextItem to Markdown format."""
        md_text = self.plain_text

        if self.annotations.bold:
            md_text = f"**{md_text}**"
        if self.annotations.italic:
            md_text = f"*{md_text}*"
        if self.annotations.strikethrough:
            md_text = f"~~{md_text}~~"
        if self.annotations.underline:
            md_text = f"__{md_text}__"
        if self.annotations.code:
            md_text = f"`{md_text}`"
        if self.href:
            md_text = f"[{md_text}]({self.href})"

        return md_text


class RichTextModel(BaseModel):
    rich_text: List[RichTextItem]

    def to_md(self) -> str:
        """Convert the entire RichTextModel to Markdown format."""
        return "".join([item.to_md() for item in self.rich_text])


class MultiSelectOption(BaseModel):
    id: str
    name: Optional[str]
    color: str

    def to_md(self) -> str:
        """Convert a single MultiSelectOption to Markdown format."""
        return f"{self.name}"


class MultiSelectProperty(BaseModel):
    multi_select: Union[Dict[Literal['options'], List[MultiSelectOption]], List[MultiSelectOption]]

    def to_md(self) -> str:
        """Convert the entire MultiSelectModel to Markdown format."""
        res = ""
        if isinstance(self.multi_select, list):
            res = ", ".join([item.to_md() for item in self.multi_select])
        elif isinstance(self.multi_select, dict):
            res = ", ".join([item.to_md() for item in self.multi_select['options']])
        return res


class SelectOption(BaseModel):
    id: str
    name: str
    color: str

    def to_md(self) -> str:
        """Convert a single SelectOption to Markdown format."""
        return self.name


class SelectProperty(BaseModel):
    select: Optional[Union[SelectOption, Dict[Literal['options'], List[SelectOption]]]]

    def to_md(self) -> str:
        """Convert the SelectModel to Markdown format."""
        if isinstance(self.select, dict):
            return ", ".join([item.to_md() for item in self.select['options']])
        elif isinstance(self.select, SelectOption):
            return self.select.to_md()
        else:
            return ""


class TitleItem(BaseModel):
    type: Literal['text']
    text: TextContent
    annotations: Annotations
    plain_text: str
    href: Optional[str] = None

    def to_md(self) -> str:
        """Convert a single RichTextItem to Markdown format."""
        md_text = self.plain_text

        if self.annotations.bold:
            md_text = f"**{md_text}**"
        if self.annotations.italic:
            md_text = f"*{md_text}*"
        if self.annotations.strikethrough:
            md_text = f"~~{md_text}~~"
        if self.annotations.underline:
            md_text = f"__{md_text}__"
        if self.annotations.code:
            md_text = f"`{md_text}`"
        if self.href:
            md_text = f"[{md_text}]({self.href})"

        return md_text


class TitleProperty(BaseModel):
    title: Union[List[TitleItem], dict]

    def to_md(self) -> str:
        """Convert the entire TitleProperty to Markdown format."""
        if isinstance(self.title, list):
            return "".join([item.to_md() for item in self.title])
        elif isinstance(self.title, dict):
            return str(dict)


class DateProperty(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    time_zone: Optional[str] = None

    def to_md(self) -> str:
        """Convert the entire DateModel to Markdown format."""
        if self.start and self.end:
            return f"{self.start.strftime('%Y-%m-%d')} ~ {self.end.strftime('%Y-%m-%d')}"
        elif self.start:
            return f"{self.start.strftime('%Y-%m-%d')}"
        elif self.end:
            return f"~ {self.end.strftime('%Y-%m-%d')}"
        else:
            return ""


class URLProperty(BaseModel):
    url: Optional[Union[str, dict]] = None

    def to_md(self) -> str:
        """Convert the entire URLModel to Markdown format."""
        return str(self.url)


class User(BaseModel):
    object: str
    id: Optional[UUID4]


class CreatedByProperty(BaseModel):
    id: Optional[User] = None

    def to_md(self) -> str:
        """Convert the CreatedBy to Markdown format."""
        return str(self.id)


class PeopleProperty(BaseModel):
    people: List[User] = []

    def to_md(self) -> str:
        """Convert the entire People to Markdown format."""
        return ", ".join([f"{user.id}" for user in self.people])


class CheckboxProperty(BaseModel):
    checkbox: bool

    def to_md(self) -> str:
        """Convert the CheckboxModel to Markdown format."""
        return '[v]' if self.checkbox else '[ ]'


class NumberProperty(BaseModel):
    number: Optional[float]

    def to_md(self) -> str:
        """Convert the NumberModel to Markdown format."""
        return str(self.number)


class CreatedTimeProperty(BaseModel):
    created_time: Optional[datetime]

    def to_md(self) -> str:
        """Convert the CreatedTime to Markdown format."""
        return str(self.created_time)


class LastEditedTimeProperty(BaseModel):
    last_edited_time: Optional[datetime]

    def to_md(self) -> str:
        """Convert the LastEditedTime to Markdown format."""
        return str(self.last_edited_time)


class StatusOption(BaseModel):
    id: str
    name: str
    color: str

    def to_md(self) -> str:
        """Convert a single StatusOption to Markdown format."""
        return self.name


class StatusModel(BaseModel):
    status: StatusOption

    def to_md(self) -> str:
        """Convert the StatusModel to Markdown format."""
        return self.status.to_md()


class Property(BaseModel):
    id: str
    type: str
    rich_text: Optional[RichTextModel] = None
    date: Optional[DateProperty] = None
    url: Optional[URLProperty] = None
    created_by: Optional[CreatedByProperty] = None
    multi_select: Optional[MultiSelectProperty] = None
    select: Optional[SelectProperty] = None
    title: Optional[TitleProperty] = None
    people: Optional[PeopleProperty] = None
    checkbox: Optional[CheckboxProperty] = None
    number: Optional[NumberProperty] = None
    created_time: Optional[CreatedTimeProperty] = None
    last_edited_time: Optional[LastEditedTimeProperty] = None
    status: Optional[StatusModel] = None

    @classmethod
    def parse_property(cls, property_id: str, property_data: dict) -> 'Property':
        type_mapping = {
            'rich_text': (RichTextModel, 'rich_text'),
            'multi_select': (MultiSelectProperty, 'multi_select'),
            'select': (SelectProperty, 'select'),
            'title': (TitleProperty, 'title'),
            'date': (DateProperty, 'date'),
            'url': (URLProperty, 'url'),
            'created_by': (CreatedByProperty, 'created_by'),
            'people': (PeopleProperty, 'people'),
            'checkbox': (CheckboxProperty, 'checkbox'),
            'number': (NumberProperty, 'number'),
            'created_time': (CreatedTimeProperty, 'created_time'),
            'last_edited_time': (LastEditedTimeProperty, 'last_edited_time'),
            'status': (StatusModel, 'status'),
        }

        type_key = property_data['type']
        model_class, data_key = type_mapping.get(type_key, (None, None))

        try:
            if model_class:
                if type_key == 'rich_text':
                    # Adjust each item in the list to have the correct 'type' value
                    adjusted_data = [{'type': 'rich_text', **item} if item.get('type') != 'rich_text' else item
                                     for item in property_data.get(data_key, [])]
                    property_data[data_key] = model_class(**{data_key: adjusted_data})
                else:
                    property_data[data_key] = model_class(**{data_key: property_data.get(data_key, [])})
            else:
                raise ValueError(f'Unknown property type: {type_key}')
        except Exception as e:
            print(property_data)
            print(property_data.get(data_key, []))
            print(e)
            raise Exception(f'Failed to parse property {property_id} of type {type_key}') from e

        property_data.pop('id', None)
        property_data.pop('type', None)

        return cls(id=property_id, type=type_key, **property_data)

    def to_md(self):
        return self.__dict__.get(self.type).to_md()


PropertyType = Union[
    RichTextModel, DateProperty, URLProperty, CreatedByProperty, MultiSelectProperty, SelectProperty, TitleProperty, PeopleProperty, CheckboxProperty, NumberProperty]


class PropertiesModel(BaseModel):
    properties: Dict[str, Property]

    @classmethod
    def parse_properties(cls, properties_dict: Dict[str, dict]) -> 'PropertiesModel':
        properties = deepcopy(properties_dict)
        parsed_properties = {prop_id: Property.parse_property(prop_id, prop_data)
                             for prop_id, prop_data in properties.items()}
        return cls(properties=parsed_properties)

    def get_property(self, item: str) -> Optional[Property]:
        return self.properties.get(item)

    def to_md(self) -> str:
        """Convert the entire PropertiesModel to Markdown format.
        First find the EmojiModel, then the TitleProperty, make # {emoji} {title} as the header,
        and the tab separated list of properties as the body.
        """
        res = self.get_title_md()

        return res + self.get_property_md()

    def get_property_md(self):
        res = ""
        for key, value in self.properties.items():
            if value.type not in ['emoji', 'title']:
                try:
                    res += f"\t{key}: {value.to_md()}\n"
                except Exception as e:
                    print(e)
                    print("---------")
                    print(key)
                    print("---------")
                    print(value)
                    print("---------")
                    print(value.type)
                    raise e
        return res

    def get_title_md(self) -> str:
        """Convert the entire PropertiesModel to Markdown format.
        First find the EmojiModel, then the TitleProperty, make # {emoji} {title} as the header"""
        emoji = None
        title = None
        for key, value in self.properties.items():
            if value.type == 'emoji':
                emoji = value
                break
            elif value.type == 'title':
                title = value
                break

        res = "# "
        if emoji:
            res += f"{emoji.emoji} "
        if title:
            res += f"{title.to_md()}"
        else:
            res += "Untitled"
        res += "\n"

        return res
#
# block = {'object': 'page', 'id': '8a4ca2ea-948d-4f52-af90-ee0f25116d9c', 'created_time': '2023-11-30T00:34:00.000Z',
#          'last_edited_time': '2023-11-30T04:24:00.000Z',
#          'created_by': {'object': 'user', 'id': 'cf982f9c-6d3f-4cfa-b3eb-fc6023f7182a'},
#          'last_edited_by': {'object': 'user', 'id': '32a7ad4c-3f3e-4a27-82d6-4ed21fdaf941'}, 'cover': None,
#          'icon': {'type': 'emoji', 'emoji': '🎟️'},
#          'parent': {'type': 'database_id', 'database_id': 'b6b049bb-cc9f-44ea-9945-ef2116b13d9d'}, 'archived': False,
#          'properties': {'Property': {'id': '%3AFM%3B', 'type': 'rich_text', 'rich_text': []},
#                         'Coupon expire_at': {'id': '%3BTiC', 'type': 'date', 'date': None},
#                         '사개팀 참고 Link': {'id': 'Gku%7C', 'type': 'url', 'url': None},
#                         'created by': {'id': 'JMRf', 'type': 'created_by',
#                                        'created_by': {'object': 'user', 'id': 'cf982f9c-6d3f-4cfa-b3eb-fc6023f7182a'}},
#                         'Duration': {'id': 'P%3C%3BE', 'type': 'multi_select', 'multi_select': [
#                             {'id': 'b2871370-3f74-48c5-b245-928ff63bceef', 'name': '12개월', 'color': 'red'}]},
#                         '\x08Available Service': {'id': 'R%60hd', 'type': 'multi_select', 'multi_select': []},
#                         '마팀 참고 Link': {'id': 'ZBO%5C', 'type': 'url', 'url': None},
#                         'Status': {'id': '%5Dcvb', 'type': 'select',
#                                    'select': {'id': '73da80d2-1d16-4cd0-ae13-6bdfb8634e08', 'name': 'upcoming',
#                                               'color': 'red'}},
#                         '그외 스펙 문서': {'id': '%5EcE%60', 'type': 'url', 'url': None},
#                         'Promotion Date': {'id': 'gfrW', 'type': 'date',
#                                            'date': {'start': '2023-12-11', 'end': '2023-12-15', 'time_zone': None}},
#                         'CouponType': {'id': 'h%7BTs', 'type': 'multi_select', 'multi_select': [
#                             {'id': '0f4f6fab-6c94-4c73-b8ba-84c80622914c', 'name': 'Regular::Tall', 'color': 'blue'}]},
#                         'Sales Page': {'id': 's~cq', 'type': 'url', 'url': None},
#                         'Name': {'id': 'title', 'type': 'title', 'title': [
#                             {'type': 'text', 'text': {'content': '위메프 12월 할인 프로모션', 'link': None},
#                              'annotations': {'bold': False, 'italic': False, 'strikethrough': False, 'underline': False,
#                                              'code': False, 'color': 'default'}, 'plain_text': '위메프 12월 할인 프로모션',
#                              'href': None}]}}, 'url': 'https://www.notion.so/12-8a4ca2ea948d4f52af90ee0f25116d9c',
#          'public_url': None}
#
# pprint(loads(PropertiesModel.parse_properties(block['properties']).model_dump_json()))
