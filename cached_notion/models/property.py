import uuid
from copy import deepcopy
from datetime import datetime
from typing import List, Dict, Literal
from typing import Optional
from typing import Union

from pydantic import BaseModel, Field, UUID4


class EmojiModel(BaseModel):
    type: Literal["emoji"]
    emoji: str


class DatabaseIDModel(BaseModel):
    type: Literal["database_id"]
    database_id: uuid.UUID


class TextContent(BaseModel):
    content: str
    link: Optional[Union[str, Dict]] = None


class Annotations(BaseModel):
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: str = "default"


class RichTextItem(BaseModel):
    """A single rich text item.

    Notion returns several item types ('text', 'mention', 'equation'); only
    'text' items carry a ``text`` payload, so everything but ``plain_text``
    (which every type provides) is parsed leniently and rendering falls back
    to ``plain_text``.
    """

    type: str = "text"
    text: Optional[TextContent] = None
    annotations: Annotations = Field(default_factory=Annotations)
    plain_text: str = ""
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
    #: A page value is a list of items; a database schema column is an empty ``{}``.
    rich_text: Union[List[RichTextItem], dict] = Field(default_factory=list)

    def to_md(self) -> str:
        """Convert the entire RichTextModel to Markdown format."""
        if isinstance(self.rich_text, list):
            return "".join([item.to_md() for item in self.rich_text])
        # A database schema exposes an empty ``{}`` payload, which has no text.
        return ""


class MultiSelectOption(BaseModel):
    id: str
    name: Optional[str] = None
    color: str

    def to_md(self) -> str:
        """Convert a single MultiSelectOption to Markdown format."""
        return self.name or ""


class MultiSelectProperty(BaseModel):
    multi_select: Optional[Union[Dict[Literal["options"], List[MultiSelectOption]], List[MultiSelectOption]]] = None

    def to_md(self) -> str:
        """Convert the entire MultiSelectModel to Markdown format."""
        res = ""
        if isinstance(self.multi_select, list):
            res = ", ".join([item.to_md() for item in self.multi_select])
        elif isinstance(self.multi_select, dict):
            res = ", ".join([item.to_md() for item in self.multi_select["options"]])
        return res


class SelectOption(BaseModel):
    id: str
    name: str
    color: str

    def to_md(self) -> str:
        """Convert a single SelectOption to Markdown format."""
        return self.name


class SelectProperty(BaseModel):
    select: Optional[Union[SelectOption, Dict[Literal["options"], List[SelectOption]]]] = None

    def to_md(self) -> str:
        """Convert the SelectModel to Markdown format."""
        if isinstance(self.select, dict):
            return ", ".join([item.to_md() for item in self.select["options"]])
        elif isinstance(self.select, SelectOption):
            return self.select.to_md()
        else:
            return ""


#: A title value is a rich text array, so its items have the same shape.
TitleItem = RichTextItem


class TitleProperty(BaseModel):
    title: Union[List[TitleItem], dict] = Field(default_factory=list)

    def to_md(self) -> str:
        """Convert the entire TitleProperty to Markdown format."""
        if isinstance(self.title, list):
            return "".join([item.to_md() for item in self.title])
        # A database schema exposes an empty ``{}`` payload, which has no text.
        return ""


class DateValue(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    time_zone: Optional[str] = None


class DateProperty(BaseModel):
    date: Optional[DateValue] = None

    def to_md(self) -> str:
        """Convert the entire DateModel to Markdown format."""
        if self.date is None:
            return ""
        start, end = self.date.start, self.date.end
        if start and end:
            return f"{start.strftime('%Y-%m-%d')} ~ {end.strftime('%Y-%m-%d')}"
        elif start:
            return f"{start.strftime('%Y-%m-%d')}"
        elif end:
            return f"~ {end.strftime('%Y-%m-%d')}"
        else:
            return ""


class URLProperty(BaseModel):
    url: Optional[Union[str, dict]] = None

    def to_md(self) -> str:
        """Convert the entire URLModel to Markdown format."""
        if not self.url or isinstance(self.url, dict):
            return ""
        return self.url


class User(BaseModel):
    object: str = "user"
    id: Optional[UUID4] = None


class CreatedByProperty(BaseModel):
    created_by: Optional[User] = None

    def to_md(self) -> str:
        """Convert the CreatedBy to Markdown format."""
        if self.created_by is None or self.created_by.id is None:
            return ""
        return str(self.created_by.id)


class PeopleProperty(BaseModel):
    people: List[User] = Field(default_factory=list)

    def to_md(self) -> str:
        """Convert the entire People to Markdown format."""
        return ", ".join([f"{user.id}" for user in self.people if user.id])


class CheckboxProperty(BaseModel):
    checkbox: bool

    def to_md(self) -> str:
        """Convert the CheckboxModel to Markdown format."""
        return "[v]" if self.checkbox else "[ ]"


class NumberProperty(BaseModel):
    number: Optional[float] = None

    def to_md(self) -> str:
        """Convert the NumberModel to Markdown format."""
        if self.number is None:
            return ""
        return str(self.number)


class CreatedTimeProperty(BaseModel):
    created_time: Optional[datetime] = None

    def to_md(self) -> str:
        """Convert the CreatedTime to Markdown format."""
        if self.created_time is None:
            return ""
        return str(self.created_time)


class LastEditedTimeProperty(BaseModel):
    last_edited_time: Optional[datetime] = None

    def to_md(self) -> str:
        """Convert the LastEditedTime to Markdown format."""
        if self.last_edited_time is None:
            return ""
        return str(self.last_edited_time)


class StatusOption(BaseModel):
    id: str
    name: str
    color: str

    def to_md(self) -> str:
        """Convert a single StatusOption to Markdown format."""
        return self.name


class StatusModel(BaseModel):
    status: Optional[StatusOption] = None

    def to_md(self) -> str:
        """Convert the StatusModel to Markdown format."""
        if self.status is None:
            return ""
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
    def parse_property(cls, property_id: str, property_data: dict) -> "Property":
        type_mapping = {
            "rich_text": (RichTextModel, "rich_text"),
            "multi_select": (MultiSelectProperty, "multi_select"),
            "select": (SelectProperty, "select"),
            "title": (TitleProperty, "title"),
            "date": (DateProperty, "date"),
            "url": (URLProperty, "url"),
            "created_by": (CreatedByProperty, "created_by"),
            "people": (PeopleProperty, "people"),
            "checkbox": (CheckboxProperty, "checkbox"),
            "number": (NumberProperty, "number"),
            "created_time": (CreatedTimeProperty, "created_time"),
            "last_edited_time": (LastEditedTimeProperty, "last_edited_time"),
            "status": (StatusModel, "status"),
        }

        type_key = property_data["type"]
        model_class, data_key = type_mapping.get(type_key, (None, None))

        try:
            if model_class:
                # A missing or null payload key falls back to the model's own defaults —
                # an explicit `[]` is not a valid payload for select/date/status/url.
                payload = property_data.get(data_key)
                property_data[data_key] = model_class(**{data_key: payload}) if payload is not None else model_class()
            else:
                raise ValueError(f"Unknown property type: {type_key}")
        except Exception as e:
            print(property_data)
            print(property_data.get(data_key, []))
            print(e)
            raise Exception(f"Failed to parse property {property_id} of type {type_key}") from e

        property_data.pop("id", None)
        property_data.pop("type", None)

        return cls(id=property_id, type=type_key, **property_data)

    def to_md(self):
        return self.__dict__.get(self.type).to_md()


PropertyType = Union[
    RichTextModel,
    DateProperty,
    URLProperty,
    CreatedByProperty,
    MultiSelectProperty,
    SelectProperty,
    TitleProperty,
    PeopleProperty,
    CheckboxProperty,
    NumberProperty,
]


class PropertiesModel(BaseModel):
    properties: Dict[str, Property]

    @classmethod
    def parse_properties(cls, properties_dict: Dict[str, dict]) -> "PropertiesModel":
        properties = deepcopy(properties_dict)
        parsed_properties = {
            prop_id: Property.parse_property(prop_id, prop_data) for prop_id, prop_data in properties.items()
        }
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
            if value.type not in ["emoji", "title"]:
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
            if value.type == "emoji":
                emoji = value
                break
            elif value.type == "title":
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
