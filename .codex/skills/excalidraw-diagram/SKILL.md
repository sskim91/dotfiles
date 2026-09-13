---
name: excalidraw-diagram
description: 편집 가능한 .excalidraw 다이어그램 파일을 만들거나 수정할 때 사용한다.
---

# Excalidraw Diagram Creator

Create an editable `.excalidraw` file whose structure explains the requested relationships. Match the user's chosen scope, visual style, and level of detail.

## Local resources

- Read [color-palette.md](references/color-palette.md) when choosing colors. It is the local palette for semantic fills, strokes, text, and evidence panels.
- Read the relevant element types in [element-templates.md](references/element-templates.md) when constructing JSON or fixing bindings.
- For a complex layout, consult [layout-patterns.md](references/layout-patterns.md). Simple diagrams do not need the pattern catalog.
- The renderer and its dependencies live in `references/`.

## Deliverable requirements

Use an Excalidraw version 2 document with `type: "excalidraw"`, `elements`, `appState`, and `files`. Keep IDs unique and all arrow/text bindings consistent with the referenced elements. Text fields contain the readable label, with `originalText` matching the intended text.

Use the local defaults (`fontFamily: 3`, `roughness: 0`, `opacity: 100`) unless the user requests a different style. Use containers when they represent a component, boundary, or grouping; use plain labels when a box adds no meaning.

Show actual component or API names when they are known. For technical facts that are missing or version-sensitive, consult the provided source or official specification. An overview can remain an overview: add payloads, code, and multiple zoom levels only when they help answer the request.

Choose a construction method suited to the size of the diagram. Large diagrams may benefit from sections and a small generator; a fixed number of edits, patterns, or containers is not required.

## Render and inspect

From this skill's `references/` directory:

```bash
uv run python render_excalidraw.py <path-to-file.excalidraw>
```

The renderer writes a PNG beside the source file. Open it with the available image viewer and check that labels are readable, arrows connect to the intended elements, and nothing clips or overlaps unintentionally. Fix observed defects and render the affected result again. Finish when the requested meaning and visual quality are satisfied; a passing first render needs no additional iterations.

If renderer dependencies are missing, set them up in `references/` using the existing project:

```bash
uv sync
uv run playwright install chromium
```

Report the editable file and preview. If rendering is unavailable, report that limitation instead of claiming the visual result was verified.
