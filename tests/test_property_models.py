"""Contract and regression tests for ``cached_notion.models.property``.

Two kinds of tests live here:

* **Contract tests** describe behaviour that must keep working. They pass today.
* **Bug tests** (``test_bug_bN_*``, plus the two ``test_realistic_page_*``
  integration tests) describe behaviour that is currently broken. They are
  expected to fail until ``property.py`` is fixed (TDD red stage).

The public entry point used by ``cached_notion/utils.py`` (``_get_page_info`` /
``_convert_entries``) is ``PropertiesModel.parse_properties(properties_dict)``
followed by ``get_title_md()`` / ``get_property_md()`` / ``to_md()``, so every
bug is also exercised through that integration path.

All fixtures are synthetic payloads shaped after the Notion API reference
(https://developers.notion.com/reference/property-value-object): every property
value is a ``{"id": ..., "type": <type>, <type>: <payload>}`` wrapper.
"""

import pytest

from cached_notion.models.property import (
    CheckboxProperty,
    CreatedByProperty,
    CreatedTimeProperty,
    DateProperty,
    LastEditedTimeProperty,
    MultiSelectProperty,
    NumberProperty,
    PeopleProperty,
    PropertiesModel,
    RichTextModel,
    SelectProperty,
    StatusModel,
    TitleProperty,
    URLProperty,
)

# --------------------------------------------------------------------------- #
# Synthetic payload builders (Notion API shapes)
# --------------------------------------------------------------------------- #

USER_ID = "00000000-0000-4000-8000-000000000001"
OTHER_USER_ID = "00000000-0000-4000-8000-000000000002"
PAGE_ID = "00000000-0000-4000-8000-00000000000a"

DEFAULT_ANNOTATIONS = {
    "bold": False,
    "italic": False,
    "strikethrough": False,
    "underline": False,
    "code": False,
    "color": "default",
}


def annotations(**overrides):
    ann = dict(DEFAULT_ANNOTATIONS)
    ann.update(overrides)
    return ann


def text_item(content="hello", href=None, link=None, **ann):
    """A ``type: "text"`` rich text item."""
    return {
        "type": "text",
        "text": {"content": content, "link": link},
        "annotations": annotations(**ann),
        "plain_text": content,
        "href": href,
    }


def user_mention_item(plain_text="@Tim", user_id=USER_ID, href=None, **ann):
    """A ``type: "mention"`` rich text item pointing at a user."""
    return {
        "type": "mention",
        "mention": {"type": "user", "user": {"object": "user", "id": user_id}},
        "annotations": annotations(**ann),
        "plain_text": plain_text,
        "href": href,
    }


def page_mention_item(plain_text="Project page", page_id=PAGE_ID, **ann):
    """A ``type: "mention"`` rich text item pointing at a page (has ``href``)."""
    return {
        "type": "mention",
        "mention": {"type": "page", "page": {"id": page_id}},
        "annotations": annotations(**ann),
        "plain_text": plain_text,
        "href": f"https://www.notion.so/{page_id.replace('-', '')}",
    }


def date_mention_item(start="2023-12-11", plain_text="2023-12-11", **ann):
    """A ``type: "mention"`` rich text item pointing at a date."""
    return {
        "type": "mention",
        "mention": {
            "type": "date",
            "date": {"start": start, "end": None, "time_zone": None},
        },
        "annotations": annotations(**ann),
        "plain_text": plain_text,
        "href": None,
    }


def equation_item(expression="E = mc^2", **ann):
    """A ``type: "equation"`` rich text item."""
    return {
        "type": "equation",
        "equation": {"expression": expression},
        "annotations": annotations(**ann),
        "plain_text": expression,
        "href": None,
    }


def partial_user(user_id=USER_ID):
    return {"object": "user", "id": user_id}


def prop(property_type, payload, property_id="Ab%3Cd"):
    """Wrap a payload the way the Notion API returns a page property value."""
    return {"id": property_id, "type": property_type, property_type: payload}


def title_prop(content="Weekly report"):
    return prop("title", [text_item(content)], property_id="title")


def schema_prop(property_type, payload, property_id="j%7CjO", name=None):
    """Wrap a payload the way the Notion API returns a *database schema* property.

    A database object's ``properties`` map describes columns, not values
    (https://developers.notion.com/reference/property-object): the per-type
    payload is a configuration object (``{}`` for text-like columns,
    ``{"options": [...]}`` for select-like ones) and the wrapper carries an
    extra ``name`` key. ``utils._traverse`` feeds these through the very same
    ``PropertiesModel.parse_properties`` entry point as page values.
    """
    return {
        "id": property_id,
        "name": name if name is not None else property_type,
        "type": property_type,
        property_type: payload,
    }


SELECT_SCHEMA_OPTIONS = {
    "options": [
        {"id": "s1", "name": "upcoming", "color": "red"},
        {"id": "s2", "name": "done", "color": "green"},
    ]
}

MULTI_SELECT_SCHEMA_OPTIONS = {
    "options": [
        {"id": "m1", "name": "12 months", "color": "red"},
        {"id": "m2", "name": "6 months", "color": "blue"},
    ]
}

STATUS_SCHEMA_OPTIONS = {
    "options": [
        {"id": "st1", "name": "Not started", "color": "default"},
        {"id": "st2", "name": "In progress", "color": "blue"},
    ],
    "groups": [
        {"id": "g1", "name": "To-do", "color": "gray", "option_ids": ["st1"]},
        {"id": "g2", "name": "In progress", "color": "blue", "option_ids": ["st2"]},
    ],
}


def database_schema_properties():
    """The ``properties`` map of a database object, covering the renderable columns."""
    return {
        "Name": schema_prop("title", {}, property_id="title", name="Name"),
        "Description": schema_prop("rich_text", {}, property_id="j%7CjO", name="Description"),
        "Stage": schema_prop("select", SELECT_SCHEMA_OPTIONS, property_id="%7CtzR", name="Stage"),
        "Tags": schema_prop("multi_select", MULTI_SELECT_SCHEMA_OPTIONS, property_id="z%40%3EO", name="Tags"),
        "Due": schema_prop("date", {}, property_id="%3DDA%3F", name="Due"),
        "Link": schema_prop("url", {}, property_id="Ass%3A", name="Link"),
        "Creator": schema_prop("created_by", {}, property_id="Ca%3EO", name="Creator"),
    }


#: Every property type ``Property.parse_property`` claims to support.
SUPPORTED_TYPES = [
    "title",
    "rich_text",
    "select",
    "multi_select",
    "status",
    "date",
    "url",
    "checkbox",
    "number",
    "people",
    "created_by",
    "created_time",
    "last_edited_time",
]


def realistic_page_properties():
    """A page whose properties cover all 13 supported types at once."""
    return {
        "Name": title_prop("Q4 promotion"),
        "Note": prop("rich_text", [text_item("cc "), user_mention_item("@Tim")], property_id="%3AFM%3B"),
        "Stage": prop("select", {"id": "s1", "name": "upcoming", "color": "red"}, property_id="%5Dcvb"),
        "Duration": prop(
            "multi_select",
            [{"id": "m1", "name": "12 months", "color": "red"}],
            property_id="P%3C%3BE",
        ),
        "Status": prop("status", None, property_id="cQ%7Cx"),
        "Promotion Date": prop(
            "date",
            {"start": "2023-12-11", "end": "2023-12-15", "time_zone": None},
            property_id="gfrW",
        ),
        "Sales Page": prop("url", "https://example.com/sales", property_id="s~cq"),
        "Done": prop("checkbox", False, property_id="%3Bkm%7C"),
        "Amount": prop("number", None, property_id="Kv%3Ac"),
        "Owners": prop("people", [partial_user(OTHER_USER_ID)], property_id="rQ%40i"),
        "created by": prop("created_by", partial_user(USER_ID), property_id="JMRf"),
        "Created": prop("created_time", "2023-11-30T00:34:00.000Z", property_id="Nj%5Eb"),
        "Edited": prop("last_edited_time", "2023-11-30T04:24:00.000Z", property_id="wE%3Fq"),
    }


# --------------------------------------------------------------------------- #
# Contract: rich text formatting
# --------------------------------------------------------------------------- #


def test_rich_text_plain_item_renders_plain_text():
    model = RichTextModel.model_validate({"rich_text": [text_item("hello")]})
    assert model.to_md() == "hello"


@pytest.mark.parametrize(
    "annotation, expected",
    [
        ("bold", "**hello**"),
        ("italic", "*hello*"),
        ("strikethrough", "~~hello~~"),
        ("underline", "__hello__"),
        ("code", "`hello`"),
    ],
)
def test_rich_text_annotation_markers(annotation, expected):
    payload = {"rich_text": [text_item("hello", **{annotation: True})]}
    assert RichTextModel.model_validate(payload).to_md() == expected


def test_rich_text_bold_and_italic_combine():
    payload = {"rich_text": [text_item("hello", bold=True, italic=True)]}
    assert RichTextModel.model_validate(payload).to_md() == "***hello***"


def test_rich_text_link_wraps_the_formatted_text():
    payload = {
        "rich_text": [
            text_item("hello", href="https://example.com", bold=True),
        ]
    }
    assert RichTextModel.model_validate(payload).to_md() == "[**hello**](https://example.com)"


def test_rich_text_items_are_concatenated_in_order():
    payload = {
        "rich_text": [
            text_item("plain "),
            text_item("bold", bold=True),
            text_item(" tail"),
        ]
    }
    assert RichTextModel.model_validate(payload).to_md() == "plain **bold** tail"


def test_rich_text_empty_list_renders_empty_string():
    assert RichTextModel.model_validate({"rich_text": []}).to_md() == ""


# --------------------------------------------------------------------------- #
# Contract: individual property models
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "model, payload, expected",
    [
        # title
        (TitleProperty, {"title": [text_item("Weekly report")]}, "Weekly report"),
        (TitleProperty, {"title": []}, ""),
        # rich_text
        (RichTextModel, {"rich_text": [text_item("note")]}, "note"),
        # select (page value and database schema shape)
        (
            SelectProperty,
            {"select": {"id": "s1", "name": "upcoming", "color": "red"}},
            "upcoming",
        ),
        (SelectProperty, {"select": None}, ""),
        (
            SelectProperty,
            {
                "select": {
                    "options": [
                        {"id": "s1", "name": "upcoming", "color": "red"},
                        {"id": "s2", "name": "done", "color": "green"},
                    ]
                }
            },
            "upcoming, done",
        ),
        # multi_select (page value and database schema shape)
        (
            MultiSelectProperty,
            {
                "multi_select": [
                    {"id": "m1", "name": "12 months", "color": "red"},
                    {"id": "m2", "name": "6 months", "color": "blue"},
                ]
            },
            "12 months, 6 months",
        ),
        (MultiSelectProperty, {"multi_select": []}, ""),
        (
            MultiSelectProperty,
            {"multi_select": {"options": [{"id": "m1", "name": "12 months", "color": "red"}]}},
            "12 months",
        ),
        # status
        (
            StatusModel,
            {"status": {"id": "st1", "name": "In progress", "color": "blue"}},
            "In progress",
        ),
        # checkbox
        (CheckboxProperty, {"checkbox": True}, "[v]"),
        (CheckboxProperty, {"checkbox": False}, "[ ]"),
        # number
        (NumberProperty, {"number": 42.5}, "42.5"),
        # url
        (URLProperty, {"url": "https://example.com/spec"}, "https://example.com/spec"),
        # date (empty value)
        (DateProperty, {"date": None}, ""),
        # people
        (PeopleProperty, {"people": []}, ""),
        (
            PeopleProperty,
            {"people": [partial_user(USER_ID), partial_user(OTHER_USER_ID)]},
            f"{USER_ID}, {OTHER_USER_ID}",
        ),
    ],
)
def test_property_model_renders_expected_markdown(model, payload, expected):
    assert model.model_validate(payload).to_md() == expected


@pytest.mark.parametrize(
    "model, key",
    [
        (CreatedTimeProperty, "created_time"),
        (LastEditedTimeProperty, "last_edited_time"),
    ],
)
def test_timestamp_properties_render_their_date(model, key):
    """Timestamps must render the actual instant (exact format left open)."""
    md = model.model_validate({key: "2023-11-30T00:34:00.000Z"}).to_md()
    assert md.startswith("2023-11-30")
    assert "None" not in md


def test_number_integer_value_renders_a_number():
    """An integer number must render as a number, never as ``None``."""
    md = NumberProperty.model_validate({"number": 42}).to_md()
    # '42' and '42.0' are both acceptable; the formatting choice is not pinned.
    assert md in {"42", "42.0"}


# --------------------------------------------------------------------------- #
# Contract: PropertiesModel.parse_properties integration path
# --------------------------------------------------------------------------- #


def test_parse_properties_keeps_keys_and_types():
    parsed = PropertiesModel.parse_properties(
        {
            "Name": title_prop("Weekly report"),
            "Done": prop("checkbox", True),
            "Note": prop("rich_text", [text_item("note")]),
        }
    )
    assert set(parsed.properties) == {"Name", "Done", "Note"}
    assert parsed.get_property("Note").type == "rich_text"
    assert parsed.get_property("Done").type == "checkbox"
    assert parsed.get_property("Missing") is None


def test_parse_properties_does_not_mutate_the_input_dict():
    payload = {"Note": prop("rich_text", [text_item("note")])}
    snapshot = {"Note": prop("rich_text", [text_item("note")])}

    PropertiesModel.parse_properties(payload)

    assert payload == snapshot


@pytest.mark.parametrize(
    "key, property_value, expected_line",
    [
        ("Note", prop("rich_text", [text_item("note")]), "\tNote: note\n"),
        ("Note", prop("rich_text", []), "\tNote: \n"),
        ("Done", prop("checkbox", True), "\tDone: [v]\n"),
        ("Done", prop("checkbox", False), "\tDone: [ ]\n"),
        ("Amount", prop("number", 42.5), "\tAmount: 42.5\n"),
        (
            "Link",
            prop("url", "https://example.com/spec"),
            "\tLink: https://example.com/spec\n",
        ),
        ("Due", prop("date", None), "\tDue: \n"),
        (
            "Stage",
            prop("select", {"id": "s1", "name": "upcoming", "color": "red"}),
            "\tStage: upcoming\n",
        ),
        ("Stage", prop("select", None), "\tStage: \n"),
        (
            "Status",
            prop("status", {"id": "st1", "name": "In progress", "color": "blue"}),
            "\tStatus: In progress\n",
        ),
        (
            "Duration",
            prop(
                "multi_select",
                [
                    {"id": "m1", "name": "12 months", "color": "red"},
                    {"id": "m2", "name": "6 months", "color": "blue"},
                ],
            ),
            "\tDuration: 12 months, 6 months\n",
        ),
        ("Duration", prop("multi_select", []), "\tDuration: \n"),
        (
            "Owners",
            prop("people", [partial_user(USER_ID)]),
            f"\tOwners: {USER_ID}\n",
        ),
        ("Owners", prop("people", []), "\tOwners: \n"),
    ],
)
def test_parse_properties_renders_property_line(key, property_value, expected_line):
    parsed = PropertiesModel.parse_properties({key: property_value})
    assert parsed.get_property_md() == expected_line


@pytest.mark.parametrize(
    "key, property_type",
    [("Created", "created_time"), ("Edited", "last_edited_time")],
)
def test_parse_properties_renders_timestamp_line(key, property_type):
    """Timestamp lines must show the instant (exact format left open)."""
    parsed = PropertiesModel.parse_properties({key: prop(property_type, "2023-11-30T00:34:00.000Z")})
    line = parsed.get_property_md()

    assert line.startswith(f"\t{key}: 2023-11-30")
    assert line.endswith("\n")
    assert "None" not in line


def test_property_to_md_delegates_to_the_typed_payload():
    parsed = PropertiesModel.parse_properties(
        {"Done": prop("checkbox", True), "Note": prop("rich_text", [text_item("note")])}
    )
    assert parsed.get_property("Done").to_md() == "[v]"
    assert parsed.get_property("Note").to_md() == "note"


def test_get_title_md_uses_the_title_property():
    parsed = PropertiesModel.parse_properties({"Name": title_prop("Weekly report")})
    assert parsed.get_title_md() == "# Weekly report\n"


def test_get_title_md_finds_the_title_even_when_it_is_not_first():
    parsed = PropertiesModel.parse_properties(
        {
            "Done": prop("checkbox", True),
            "Amount": prop("number", 1.0),
            "Name": title_prop("Weekly report"),
        }
    )
    assert parsed.get_title_md() == "# Weekly report\n"


def test_get_title_md_keeps_rich_text_formatting():
    parsed = PropertiesModel.parse_properties(
        {"Name": prop("title", [text_item("Weekly", bold=True), text_item(" report")], property_id="title")}
    )
    assert parsed.get_title_md() == "# **Weekly** report\n"


def test_get_title_md_falls_back_to_untitled():
    parsed = PropertiesModel.parse_properties({"Done": prop("checkbox", True)})
    assert parsed.get_title_md() == "# Untitled\n"


def test_get_title_md_on_empty_properties():
    assert PropertiesModel.parse_properties({}).get_title_md() == "# Untitled\n"


def test_get_property_md_excludes_title_and_preserves_order():
    parsed = PropertiesModel.parse_properties(
        {
            "Name": title_prop("Weekly report"),
            "Done": prop("checkbox", True),
            "Amount": prop("number", 1.5),
        }
    )
    assert parsed.get_property_md() == "\tDone: [v]\n\tAmount: 1.5\n"


def test_get_property_md_on_empty_properties():
    assert PropertiesModel.parse_properties({}).get_property_md() == ""


def test_to_md_is_title_followed_by_properties():
    parsed = PropertiesModel.parse_properties(
        {
            "Name": title_prop("Weekly report"),
            "Done": prop("checkbox", False),
        }
    )
    assert parsed.to_md() == "# Weekly report\n\tDone: [ ]\n"


def test_entry_point_usage_matches_utils_get_page_info():
    """Mirrors cached_notion/utils.py ``_get_page_info`` (lines 143-150)."""
    page = {
        "object": "page",
        "id": PAGE_ID,
        "properties": {
            "Name": title_prop("Weekly report"),
            "Done": prop("checkbox", True),
        },
        "url": f"https://www.notion.so/{PAGE_ID}",
        "parent": {"type": "block_id", "block_id": "1c2ae1b4-8b1a-4ca4-9a6c-1f0f9c66a111"},
    }

    properties = PropertiesModel.parse_properties(page.get("properties", {}))

    assert properties.get_title_md() == "# Weekly report\n"
    assert properties.get_property_md() == "\tDone: [v]\n"


def test_entry_point_usage_matches_utils_convert_entries():
    """Mirrors cached_notion/utils.py ``_convert_entries`` (lines 306-313)."""
    entries = [
        {
            "object": "page",
            "id": PAGE_ID,
            "properties": {"Name": title_prop("Row one"), "Done": prop("checkbox", True)},
        },
        {
            "object": "page",
            "id": OTHER_USER_ID,
            "properties": {"Name": title_prop("Row two"), "Done": prop("checkbox", False)},
        },
    ]

    res = "\n".join(PropertiesModel.parse_properties(entry["properties"]).to_md() for entry in entries)

    assert res == "# Row one\n\tDone: [v]\n\n# Row two\n\tDone: [ ]\n"


# --------------------------------------------------------------------------- #
# Integration: a page using every supported property type (B2 + B3 + B4 + B5 + B6)
# --------------------------------------------------------------------------- #


def test_realistic_page_parses_every_supported_property_type():
    """Red today: the empty ``status`` (B4) and the mention in ``rich_text`` (B2) raise."""
    parsed = PropertiesModel.parse_properties(realistic_page_properties())

    assert set(parsed.properties) == set(realistic_page_properties())
    assert {p.type for p in parsed.properties.values()} == set(SUPPORTED_TYPES)


def test_realistic_page_renders_every_supported_property_type():
    """Red today: covers B2 (mention), B3 (date), B4 (status), B5 (created_by), B6 (None)."""
    md = PropertiesModel.parse_properties(realistic_page_properties()).to_md()

    assert md.startswith("# Q4 promotion\n")
    for expected_line in [
        "\tNote: cc @Tim\n",
        "\tStage: upcoming\n",
        "\tDuration: 12 months\n",
        "\tStatus: \n",
        "\tPromotion Date: 2023-12-11 ~ 2023-12-15\n",
        "\tSales Page: https://example.com/sales\n",
        "\tDone: [ ]\n",
        "\tAmount: \n",
        f"\tOwners: {OTHER_USER_ID}\n",
        f"\tcreated by: {USER_ID}\n",
    ]:
        assert expected_line in md
    assert "\tCreated: 2023-11-30" in md
    assert "\tEdited: 2023-11-30" in md
    assert "None" not in md
    assert "\tName:" not in md  # the title is the header, never a property line


# --------------------------------------------------------------------------- #
# B1: TitleProperty.to_md returns ``str(dict)`` for a dict payload
# --------------------------------------------------------------------------- #


def test_bug_b1_dict_title_payload_does_not_render_python_class_repr():
    """A database-schema title payload (``{"title": {}}``) must render ''."""
    assert TitleProperty.model_validate({"title": {}}).to_md() == ""


def test_bug_b1_dict_title_payload_through_parse_properties():
    parsed = PropertiesModel.parse_properties({"Name": {"id": "title", "type": "title", "title": {}}})
    title_md = parsed.get_title_md()

    assert "dict" not in title_md
    assert "class" not in title_md
    assert title_md.startswith("# ")
    assert title_md.endswith("\n")


# --------------------------------------------------------------------------- #
# B2: mention / equation rich text items raise ValidationError
# --------------------------------------------------------------------------- #


def test_bug_b2_rich_text_accepts_user_mention_item():
    payload = {"rich_text": [user_mention_item("@Tim")]}
    assert RichTextModel.model_validate(payload).to_md() == "@Tim"


def test_bug_b2_rich_text_accepts_equation_item():
    payload = {"rich_text": [equation_item("E = mc^2")]}
    assert RichTextModel.model_validate(payload).to_md() == "E = mc^2"


def test_bug_b2_rich_text_accepts_date_mention_item():
    payload = {"rich_text": [date_mention_item("2023-12-11", "2023-12-11")]}
    assert RichTextModel.model_validate(payload).to_md() == "2023-12-11"


def test_bug_b2_rich_text_mixes_text_mention_and_equation_in_order():
    payload = {
        "rich_text": [
            text_item("reviewed by "),
            user_mention_item("@Tim"),
            text_item(" using "),
            equation_item("E = mc^2"),
        ]
    }
    assert RichTextModel.model_validate(payload).to_md() == "reviewed by @Tim using E = mc^2"


def test_bug_b2_mention_keeps_annotations():
    payload = {"rich_text": [user_mention_item("@Tim", bold=True)]}
    assert RichTextModel.model_validate(payload).to_md() == "**@Tim**"


def test_bug_b2_page_mention_keeps_href():
    item = page_mention_item("Project page")
    payload = {"rich_text": [item]}
    assert RichTextModel.model_validate(payload).to_md() == f"[Project page]({item['href']})"


def test_bug_b2_title_accepts_mention_item():
    payload = {"title": [text_item("Report for "), user_mention_item("@Tim")]}
    assert TitleProperty.model_validate(payload).to_md() == "Report for @Tim"


def test_bug_b2_rich_text_mention_through_parse_properties():
    parsed = PropertiesModel.parse_properties(
        {"Note": prop("rich_text", [text_item("cc "), user_mention_item("@Tim")])}
    )
    assert parsed.get_property_md() == "\tNote: cc @Tim\n"


def test_bug_b2_rich_text_equation_through_parse_properties():
    parsed = PropertiesModel.parse_properties({"Note": prop("rich_text", [equation_item("E = mc^2")])})
    assert parsed.get_property_md() == "\tNote: E = mc^2\n"


def test_bug_b2_title_mention_through_parse_properties():
    parsed = PropertiesModel.parse_properties({"Name": prop("title", [user_mention_item("@Tim")], property_id="title")})
    assert parsed.get_title_md() == "# @Tim\n"


# --------------------------------------------------------------------------- #
# B3: DateProperty silently drops the nested ``date`` payload
# --------------------------------------------------------------------------- #


def test_bug_b3_date_range_renders_start_and_end():
    payload = {"date": {"start": "2023-12-11", "end": "2023-12-15", "time_zone": None}}
    assert DateProperty.model_validate(payload).to_md() == "2023-12-11 ~ 2023-12-15"


def test_bug_b3_date_start_only_renders_start():
    payload = {"date": {"start": "2023-12-11", "end": None, "time_zone": None}}
    assert DateProperty.model_validate(payload).to_md() == "2023-12-11"


def test_bug_b3_date_end_only_renders_end():
    payload = {"date": {"start": None, "end": "2023-12-15", "time_zone": None}}
    assert DateProperty.model_validate(payload).to_md() == "~ 2023-12-15"


def test_bug_b3_datetime_with_timezone_renders_the_day():
    payload = {
        "date": {
            "start": "2023-12-11T09:00:00.000+09:00",
            "end": None,
            "time_zone": "Asia/Seoul",
        }
    }
    assert DateProperty.model_validate(payload).to_md() == "2023-12-11"


def test_bug_b3_date_range_through_parse_properties():
    parsed = PropertiesModel.parse_properties(
        {"Promotion Date": prop("date", {"start": "2023-12-11", "end": "2023-12-15", "time_zone": None})}
    )
    assert parsed.get_property_md() == "\tPromotion Date: 2023-12-11 ~ 2023-12-15\n"


def test_bug_b3_date_start_only_through_parse_properties():
    parsed = PropertiesModel.parse_properties(
        {"Due": prop("date", {"start": "2023-12-11", "end": None, "time_zone": None})}
    )
    assert parsed.get_property_md() == "\tDue: 2023-12-11\n"


# --------------------------------------------------------------------------- #
# B4: StatusModel requires a status option, so an empty status crashes
# --------------------------------------------------------------------------- #


def test_bug_b4_empty_status_parses_and_renders_empty_string():
    assert StatusModel.model_validate({"status": None}).to_md() == ""


def test_bug_b4_empty_status_through_parse_properties():
    parsed = PropertiesModel.parse_properties({"Status": prop("status", None)})
    assert parsed.get_property_md() == "\tStatus: \n"


def test_bug_b4_page_with_empty_status_still_renders_title():
    parsed = PropertiesModel.parse_properties(
        {
            "Name": title_prop("Weekly report"),
            "Status": prop("status", None),
        }
    )
    assert parsed.to_md() == "# Weekly report\n\tStatus: \n"


# --------------------------------------------------------------------------- #
# B5: CreatedByProperty field name does not match the payload
# --------------------------------------------------------------------------- #


def test_bug_b5_created_by_renders_the_user_id():
    payload = {"created_by": partial_user(USER_ID)}
    assert CreatedByProperty.model_validate(payload).to_md() == USER_ID


def test_bug_b5_created_by_through_parse_properties():
    parsed = PropertiesModel.parse_properties({"created by": prop("created_by", partial_user(USER_ID))})
    assert parsed.get_property_md() == f"\tcreated by: {USER_ID}\n"


# --------------------------------------------------------------------------- #
# B6: empty values render the string ``"None"`` instead of ``""``
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "model, payload",
    [
        (NumberProperty, {"number": None}),
        (URLProperty, {"url": None}),
        (CreatedTimeProperty, {"created_time": None}),
        (LastEditedTimeProperty, {"last_edited_time": None}),
        (CreatedByProperty, {"created_by": None}),
    ],
    ids=["number", "url", "created_time", "last_edited_time", "created_by"],
)
def test_bug_b6_empty_value_renders_empty_string(model, payload):
    assert model.model_validate(payload).to_md() == ""


@pytest.mark.parametrize(
    "key, property_value",
    [
        ("Amount", prop("number", None)),
        ("Link", prop("url", None)),
        ("Created", prop("created_time", None)),
        ("Edited", prop("last_edited_time", None)),
        ("created by", prop("created_by", None)),
    ],
    ids=["number", "url", "created_time", "last_edited_time", "created_by"],
)
def test_bug_b6_empty_value_through_parse_properties(key, property_value):
    parsed = PropertiesModel.parse_properties({key: property_value})
    assert parsed.get_property_md() == f"\t{key}: \n"


# --------------------------------------------------------------------------- #
# B7: SelectProperty.select has no default (required-nullable in pydantic v2)
# --------------------------------------------------------------------------- #


def test_bug_b7_select_defaults_to_none_and_renders_empty_string():
    model = SelectProperty.model_validate({})
    assert model.select is None
    assert model.to_md() == ""


def test_bug_b7_explicit_null_select_payload_parses_and_renders_empty_string():
    """Verification half of B7: an explicit ``"select": null`` page value."""
    parsed = PropertiesModel.parse_properties({"Stage": prop("select", None)})
    assert parsed.get_property_md() == "\tStage: \n"


# --------------------------------------------------------------------------- #
# B8: parse_property's ``[]`` fallback defeats the model defaults when the
# typed payload key is missing entirely — ``[]`` is not a valid payload for
# select/date/status/url, so those four crash instead of rendering ''.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "key, property_type, expected_line",
    [
        ("Stage", "select", "\tStage: \n"),
        ("Due", "date", "\tDue: \n"),
        ("Status", "status", "\tStatus: \n"),
        ("Link", "url", "\tLink: \n"),
    ],
    ids=["select", "date", "status", "url"],
)
def test_bug_b8_missing_payload_key_parses_and_renders_empty(key, property_type, expected_line):
    """A wrapper without its typed payload key must fall back to the model default."""
    parsed = PropertiesModel.parse_properties({key: {"id": "x", "type": property_type}})
    assert parsed.get_property_md() == expected_line


# --------------------------------------------------------------------------- #
# Database schema payloads: parse_properties also receives *schemas*, not only
# page values (utils.py ``_traverse`` routes ``object == "database"`` through
# ``_get_page`` -> ``_get_page_info`` -> ``parse_properties``, and
# ``_get_page_info`` re-raises, so one unparsable column aborts ``url_to_md``).
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "key, schema_value, expected_line",
    [
        (
            "Description",
            schema_prop("rich_text", {}, property_id="j%7CjO", name="Description"),
            "\tDescription: \n",
        ),
        ("Link", schema_prop("url", {}, property_id="Ass%3A", name="Link"), "\tLink: \n"),
        ("Due", schema_prop("date", {}, property_id="%3DDA%3F", name="Due"), "\tDue: \n"),
        (
            "Stage",
            schema_prop("select", SELECT_SCHEMA_OPTIONS, property_id="%7CtzR", name="Stage"),
            "\tStage: upcoming, done\n",
        ),
        (
            "Tags",
            schema_prop("multi_select", MULTI_SELECT_SCHEMA_OPTIONS, property_id="z%40%3EO", name="Tags"),
            "\tTags: 12 months, 6 months\n",
        ),
        (
            "Creator",
            schema_prop("created_by", {}, property_id="Ca%3EO", name="Creator"),
            "\tCreator: \n",
        ),
    ],
    ids=["rich_text", "url", "date", "select", "multi_select", "created_by"],
)
def test_database_schema_property_renders_a_line(key, schema_value, expected_line):
    """Red for ``rich_text``: ``{"rich_text": {}}`` must not raise, it renders ''."""
    parsed = PropertiesModel.parse_properties({key: schema_value})
    assert parsed.get_property_md() == expected_line


def test_database_schema_title_column_renders_a_header():
    """A schema title column is ``{"title": {}}`` -- an empty header, never a repr."""
    parsed = PropertiesModel.parse_properties({"Name": schema_prop("title", {}, property_id="title", name="Name")})
    title_md = parsed.get_title_md()

    assert title_md == "# \n"
    assert parsed.get_property_md() == ""


def test_database_schema_parses_and_renders_through_parse_properties():
    """Red today: a text column (``rich_text: {}``) makes the whole database abort."""
    md = PropertiesModel.parse_properties(database_schema_properties()).to_md()

    assert md == (
        "# \n"
        "\tDescription: \n"
        "\tStage: upcoming, done\n"
        "\tTags: 12 months, 6 months\n"
        "\tDue: \n"
        "\tLink: \n"
        "\tCreator: \n"
    )
    assert "dict" not in md
    assert "None" not in md


def test_entry_point_usage_matches_utils_get_page_info_for_a_database():
    """Mirrors utils.py ``_traverse`` (326-329) -> ``_get_page_info`` (143-147)."""
    database = {
        "object": "database",
        "id": PAGE_ID,
        "properties": database_schema_properties(),
        "url": f"https://www.notion.so/{PAGE_ID.replace('-', '')}",
        "parent": {"type": "page_id", "page_id": "1c2ae1b4-8b1a-4ca4-9a6c-1f0f9c66a111"},
    }

    properties = PropertiesModel.parse_properties(database.get("properties", {}))

    assert properties.get_title_md() == "# \n"
    assert properties.get_property_md().startswith("\tDescription: \n")


@pytest.mark.parametrize(
    "key, schema_value",
    [
        ("Done", schema_prop("checkbox", {}, property_id="%40%3FOK", name="Done")),
        ("Owners", schema_prop("people", {}, property_id="%40Zpj", name="Owners")),
        ("Amount", schema_prop("number", {"format": "number"}, property_id="%7B%5D_P", name="Amount")),
        ("Created", schema_prop("created_time", {}, property_id="eB_%7D", name="Created")),
        ("Edited", schema_prop("last_edited_time", {}, property_id="%3CJ%3E%7D", name="Edited")),
        ("Status", schema_prop("status", STATUS_SCHEMA_OPTIONS, property_id="biOx", name="Status")),
    ],
    ids=["checkbox", "people", "number", "created_time", "last_edited_time", "status"],
)
def test_database_schema_property_is_not_supported_yet(key, schema_value):
    """Characterisation, not an endorsement.

    These schema shapes raise today and raised identically before the pydantic
    rework, so they are pinned here to keep the *renderable* set above honest
    and to make any future widening of support a deliberate, visible change.
    """
    with pytest.raises(Exception, match=f"Failed to parse property {key}"):
        PropertiesModel.parse_properties({key: schema_value})
