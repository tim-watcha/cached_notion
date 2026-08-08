# CLAUDE.md

> **Documentation principle**: Record only what cannot be learned from code/config files and is not guaranteed by tools, the harness, or the model (conventions, domain knowledge, pitfalls). Structure and listings are not enumerated here — they have their own sources; brevity is intentional omission. Apply the same standard when adding content.

## End goal

Provide a caching client that performs the job of **repeatedly reading large Notion page trees in full and exporting them to Markdown** with a minimum of Notion API calls. It is a drop-in replacement for `notion_client.Client`, using `last_edited_time` as the change-detection signal so only changed subtrees are re-read (1 root call when nothing changed; extra calls only for the changes).

## Architecture decision — stay dict-based (finalized 2026-08-08)

- The pipeline (cache, traversal, block rendering) is **dict-based**. Reasons: ① a read-only export tool should skip unknown input (partial success > crash) ② the Notion block schema is open-ended, so strict models break with every new type ③ cache entries grow by appending fields onto the original dicts, so a pydantic round-trip loses extra fields.
- pydantic is used **only in the property rendering layer (`cached_notion/models/property.py`)**.
- Full pydantic modeling of blocks/pages was attempted in 2023-12 and abandoned. The unfinished work is preserved on the `archive/pydantic-models-wip` branch. **Do not attempt full modeling again** — if type safety becomes necessary, go the `TypedDict(total=False)` direction.

## Cache invariants (intent that must not be broken)

- A cache entry is a document that **grows by appending** `children`/`entries`/`*_completed`/`cached_time` onto the API response. When a response's `last_edited_time` equals the cached one, the entry is not overwritten — deliberate behavior to preserve the accumulated tree.
- Passing child objects obtained from a parent listing as the `cached=` hint during traversal is the core of subtree pruning. A retrieve without a hint always calls the API.
