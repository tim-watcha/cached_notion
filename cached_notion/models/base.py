from typing import Optional, Union, Literal, Dict

from pydantic import BaseModel, Field


class Annotations(BaseModel):
    bold: bool
    italic: bool
    strikethrough: bool
    underline: bool
    code: bool
    color: str


class TextContent(BaseModel):
    content: str
    link: Optional[Dict[Literal['url'], str]]


class EquationContent(BaseModel):
    expression: str


class DatabaseMention(BaseModel):
    id: str


class DateMention(BaseModel):
    start: str
    end: Optional[str]


class LinkPreviewMention(BaseModel):
    url: str


class PageMention(BaseModel):
    id: str


class TemplateMentionDate(BaseModel):
    template_mention_date: str


class TemplateMentionUser(BaseModel):
    template_mention_user: str


class UserMention(BaseModel):
    object: str
    id: str


class MentionContent(BaseModel):
    type: str
    database: Optional[DatabaseMention]
    date: Optional[DateMention]
    link_preview: Optional[LinkPreviewMention]
    page: Optional[PageMention]
    template_mention: Optional[Union[TemplateMentionDate, TemplateMentionUser]]
    user: Optional[UserMention]


class RichText(BaseModel):
    type: Literal['text', 'mention', 'equation'] = Field(description="Type of rich text")
    text: Optional[TextContent] = Field(None, description="Text content of the rich text")
    equation: Optional[EquationContent] = Field(None, description="Equation content of the rich text")
    annotations: Annotations = Field(description="Annotations of the rich text")
    plain_text: str = Field(description="Plain text of the rich text")
    href: Optional[str] = Field(None, description="Hyperlink of the rich text")

    def to_md(self) -> str:
        md_text = self.plain_text

        # Apply Markdown formatting for annotations
        if self.annotations.bold:
            md_text = f"**{md_text}**"
        if self.annotations.italic:
            md_text = f"*{md_text}*"
        if self.annotations.strikethrough:
            md_text = f"~~{md_text}~~"
        if self.annotations.underline:
            # Markdown doesn't have underline, so we use HTML
            md_text = f"<u>{md_text}</u>"
        if self.annotations.code:
            md_text = f"`{md_text}`"

        # Hyperlink formatting, if href is available
        if self.href:
            md_text = f"[{md_text}]({self.href})"

        # Formatting for specific rich text types
        if self.type == 'equation':
            md_text = f"${self.equation.expression}$" if self.equation else md_text
        elif self.type == 'mention' and self.mention:
            # Example handling for different mentions, can be expanded
            if self.mention.type == 'user':
                md_text = f"@{md_text}"
            elif self.mention.type == 'date':
                md_text = f"{md_text} (Date Mention)"
            # Other mention types can be formatted similarly

        return md_text
