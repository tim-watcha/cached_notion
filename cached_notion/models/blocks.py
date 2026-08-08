from enum import Enum
from typing import List
from typing import Literal, Optional

from pydantic import BaseModel, Field

from cached_notion.models.base import RichText, DatabaseMention, DateMention, LinkPreviewMention, PageMention, \
    UserMention
from cached_notion.models.property import RichTextModel


class BookmarkBlock(BaseModel):
    type: Literal['bookmark']
    caption: List[RichText]
    url: str


class BreadcrumbBlock(BaseModel):
    type: Literal['breadcrumb']
    breadcrumb: dict  # Empty as per the description


class Color(str, Enum):
    blue = "blue"
    blue_background = "blue_background"
    brown = "brown"
    brown_background = "brown_background"
    default = "default"
    gray = "gray"
    gray_background = "gray_background"
    green = "green"
    green_background = "green_background"
    orange = "orange"
    orange_background = "orange_background"
    yellow = "yellow"
    pink = "pink"
    pink_background = "pink_background"
    purple = "purple"
    purple_background = "purple_background"
    red = "red"
    red_background = "red_background"
    yellow_background = "yellow_background"


class Icon(BaseModel):
    emoji: Optional[str]
    file_link: Optional[str]


class BulletedListItemBlock(BaseModel):
    rich_text: List[RichText]
    color: Color
    children: Optional[List['Block']] = None

    def to_md(self, indent=0):
        return f"- {self.rich_text[0].plain_text}"


class CalloutBlock(BaseModel):
    type: Literal['callout']
    rich_text: List[RichText]
    icon: Optional[Icon]
    color: Color


class ChildDatabaseBlock(BaseModel):
    title: str


class ChildPageBlock(BaseModel):
    title: str


class CodeBlock(BaseModel):
    caption: List[RichText]
    rich_text: List[RichText]
    language: str


class ColumnListBlock(BaseModel):
    column_list: dict


class ColumnBlock(BaseModel):
    column: dict


class DividerBlock(BaseModel):
    divider: dict


class EmbedBlock(BaseModel):
    url: str


class EquationBlock(BaseModel):
    expression: str


class FileObject(BaseModel):
    url: str


class FileBlock(BaseModel):
    type: Literal['file']
    caption: List[RichText]
    file_type: Literal['file', 'external']
    external: Optional[FileObject]
    name: str


class HeadingBlock(BaseModel):
    rich_text: List[RichText]
    color: Color
    is_toggleable: bool


class Heading1Block(HeadingBlock):
    def to_md(self, indent):
        return "  " * indent + f"# {self.rich_text[0].plain_text}"


class Heading2Block(HeadingBlock):
    def to_md(self, indent):
        return "  " * indent + f"## {self.rich_text[0].plain_text}"


class Heading3Block(HeadingBlock):
    def to_md(self, indent):
        return "  " * indent + f"### {self.rich_text[0].plain_text}"


# Image Block Model
class ImageObject(BaseModel):
    url: str


class ImageBlock(BaseModel):
    type: Literal['image']
    image: ImageObject


class LinkPreviewBlock(BaseModel):
    type: Literal['link_preview']
    url: str


class MentionBlock(BaseModel):
    type: Literal['database', 'date', 'link_preview', 'page', 'user']
    database: Optional[DatabaseMention]
    date: Optional[DateMention]
    link_preview: Optional[LinkPreviewMention]
    page: Optional[PageMention]
    user: Optional[UserMention]


class NumberedListItemBlock(BaseModel):
    rich_text: List[RichText]
    color: Color  # Assuming Color enum is already defined
    children: Optional[List['Block']] = Field(None, description="Children of the block")


class ParagraphBlock(BaseModel):
    rich_text: List[RichText]
    color: Color
    children: Optional[List['Block']] = Field(None, description="Children of the block")

    def to_md(self, indent):
        text = "  " * indent + "".join([rt.to_md() for rt in self.rich_text])
        if self.children:
            children = "  " * indent + "  \n".join([child.to_md() for child in self.children])
            return f"{text}\n{children}"
        return text


class PDFObject(BaseModel):
    url: str


class PDFBlock(BaseModel):
    caption: RichTextModel
    pdf_type: Literal['external', 'file']
    external: Optional[PDFObject]
    file: Optional[PDFObject]


class QuoteBlock(BaseModel):
    rich_text: List[RichText]
    color: Color  # Assuming Color enum is already defined
    children: Optional[List['Block']]


class SyncedFrom(BaseModel):
    block_id: Optional[str]


class SyncedBlock(BaseModel):
    synced_from: Optional[SyncedFrom]
    children: Optional[List['Block']]


# Existing definitions for RichText and other models remain the same

class TableCell(BaseModel):
    cells: List[List[RichText]]


class TableBlock(BaseModel):
    table_width: int
    has_column_header: bool
    has_row_header: bool


class TableRowBlock(BaseModel):
    table_row: TableCell


class TableOfContentsBlock(BaseModel):
    color: Color


class TemplateBlock(BaseModel):
    rich_text: List[RichText]
    children: Optional[List['Block']]


class ToDoBlock(BaseModel):
    rich_text: List[RichText]
    checked: Optional[bool]
    color: Color
    children: Optional[List['Block']]


class ToggleBlock(BaseModel):
    rich_text: List[RichText]
    color: Color


class VideoObject(BaseModel):
    url: str


class VideoBlock(BaseModel):
    video_type: Literal['external', 'file']
    external: Optional[VideoObject]
    file: Optional[VideoObject]


class Block(BaseModel):
    type: Literal[
        'bookmark', 'breadcrumb', 'bulleted_list_item', 'callout', 'child_database', 'child_page', 'code',
        'column_list', 'column', 'divider', 'embed', 'equation', 'file', 'heading_1', 'heading_2', 'heading_3',
        'image', 'link_preview', 'mention', 'numbered_list_item', 'paragraph', 'pdf', 'quote', 'synced_block',
        'table', 'table_row', 'table_of_contents', 'template', 'to_do', 'toggle', 'video']
    bookmark: Optional[BookmarkBlock] = None
    breadcrumb: Optional[BreadcrumbBlock] = None
    bulleted_list_item: Optional[BulletedListItemBlock] = None
    callout: Optional[CalloutBlock] = None
    child_database: Optional[ChildDatabaseBlock] = None
    child_page: Optional[ChildPageBlock] = None
    code: Optional[CodeBlock] = None
    column_list: Optional[ColumnListBlock] = None
    column: Optional[ColumnBlock] = None
    divider: Optional[DividerBlock] = None
    embed: Optional[EmbedBlock] = None
    equation: Optional[EquationBlock] = None
    file: Optional[FileBlock] = None
    heading_1: Optional[Heading1Block] = None
    heading_2: Optional[Heading2Block] = None
    heading_3: Optional[Heading3Block] = None
    image: Optional[ImageBlock] = None
    link_preview: Optional[LinkPreviewBlock] = None
    mention: Optional[MentionBlock] = None
    numbered_list_item: Optional[NumberedListItemBlock] = None
    paragraph: Optional[ParagraphBlock] = None
    pdf: Optional[PDFBlock] = None
    quote: Optional[QuoteBlock] = None
    synced_block: Optional[SyncedBlock] = None
    table: Optional[TableBlock] = None
    table_row: Optional[TableRowBlock] = None
    table_of_contents: Optional[TableOfContentsBlock] = None
    template: Optional[TemplateBlock] = None
    to_do: Optional[ToDoBlock] = None
    toggle: Optional[ToggleBlock] = None
    video: Optional[VideoBlock] = None

    def to_md(self, indent):
        if self.type == "paragraph":
            return self.paragraph.to_md(indent)
        elif self.type == "bulleted_list_item":
            return self.bulleted_list_item.to_md(indent)
        elif self.type == "heading_1":
            return self.heading_1.to_md(indent)
        elif self.type == "heading_2":
            return self.heading_2.to_md(indent)
        elif self.type == "heading_3":
            return self.heading_3.to_md(indent)
        else:
            print(self.type)
            raise NotImplementedError


Block.model_rebuild()
