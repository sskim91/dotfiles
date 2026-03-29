---
name: excalidraw-diagram
description: Create Excalidraw diagram JSON files that make visual arguments. Use when the user wants to visualize workflows, architectures, or concepts. Use when user says "다이어그램", "diagram", "excalidraw", "시각화", "아키텍처 그려". Do NOT use for Mermaid diagrams or draw.io.
---

# Excalidraw Diagram Creator

Generate `.excalidraw` JSON files that **argue visually**, not just display information.

**Setup:** If the user asks you to set up this skill (renderer, dependencies, etc.), see below for instructions.

## Customization

**All colors and brand-specific styles live in one file:** `references/color-palette.md`. Read it before generating any diagram and use it as the single source of truth for all color choices — shape fills, strokes, text colors, evidence artifact backgrounds, everything.

To make this skill produce diagrams in your own brand style, edit `color-palette.md`. Everything else in this file is universal design methodology and Excalidraw best practices.

---

## Core Philosophy

**Diagrams should ARGUE, not DISPLAY.**

A diagram isn't formatted text. It's a visual argument that shows relationships, causality, and flow that words alone can't express. The shape should BE the meaning.

**The Isomorphism Test**: If you removed all text, would the structure alone communicate the concept? If not, redesign.

**The Education Test**: Could someone learn something concrete from this diagram, or does it just label boxes? A good diagram teaches—it shows actual formats, real event names, concrete examples.

---

## Depth Assessment (Do This First)

Before designing, determine what level of detail this diagram needs:

### Simple/Conceptual Diagrams
Use abstract shapes when:
- Explaining a mental model or philosophy
- The audience doesn't need technical specifics
- The concept IS the abstraction (e.g., "separation of concerns")

### Comprehensive/Technical Diagrams
Use concrete examples when:
- Diagramming a real system, protocol, or architecture
- The diagram will be used to teach or explain
- The audience needs to understand what things actually look like
- You're showing how multiple technologies integrate

**For technical diagrams, you MUST include evidence artifacts** (see below).

---

## Research Mandate (For Technical Diagrams)

**Before drawing anything technical, research the actual specifications.**

If you're diagramming a protocol, API, or framework:
1. Look up the actual JSON/data formats
2. Find the real event names, method names, or API endpoints
3. Understand how the pieces actually connect
4. Use real terminology, not generic placeholders

Bad: "Protocol" -> "Frontend"
Good: "AG-UI streams events (RUN_STARTED, STATE_DELTA, A2UI_UPDATE)" -> "CopilotKit renders via createA2UIMessageRenderer()"

---

## Evidence Artifacts

Evidence artifacts are concrete examples that prove your diagram is accurate and help viewers learn. Include them in technical diagrams.

| Artifact Type | When to Use | How to Render |
|---------------|-------------|---------------|
| **Code snippets** | APIs, integrations, implementation details | Dark rectangle + syntax-colored text |
| **Data/JSON examples** | Data formats, schemas, payloads | Dark rectangle + colored text |
| **Event/step sequences** | Protocols, workflows, lifecycles | Timeline pattern (line + dots + labels) |
| **UI mockups** | Showing actual output/results | Nested rectangles mimicking real UI |
| **Real input content** | Showing what goes IN to a system | Rectangle with sample content visible |
| **API/method names** | Real function calls, endpoints | Use actual names from docs |

The key principle: **show what things actually look like**, not just what they're called.

---

## Multi-Zoom Architecture

Comprehensive diagrams operate at multiple zoom levels simultaneously.

### Level 1: Summary Flow
A simplified overview showing the full pipeline or process at a glance.

### Level 2: Section Boundaries
Labeled regions that group related components.

### Level 3: Detail Inside Sections
Evidence artifacts, code snippets, and concrete examples within each section.

**For comprehensive diagrams, aim to include all three levels.**

### Bad vs Good

| Bad (Displaying) | Good (Arguing) |
|------------------|----------------|
| 5 equal boxes with labels | Each concept has a shape that mirrors its behavior |
| Card grid layout | Visual structure matches conceptual structure |
| Icons decorating text | Shapes that ARE the meaning |
| Same container for everything | Distinct visual vocabulary per concept |

---

## Container vs. Free-Floating Text

**Not every piece of text needs a shape around it.** Default to free-floating text. Add containers only when they serve a purpose.

| Use a Container When... | Use Free-Floating Text When... |
|------------------------|-------------------------------|
| It's the focal point of a section | It's a label or description |
| It needs visual grouping with other elements | It's supporting detail or metadata |
| Arrows need to connect to it | It describes something nearby |
| The shape itself carries meaning | It's a section title, subtitle, or annotation |

**The container test**: For each boxed element, ask "Would this work as free-floating text?" If yes, remove the container.

---

## Design Process (Do This BEFORE Generating JSON)

### Step 0: Assess Depth Required
- **Simple/Conceptual**: Abstract shapes, labels, relationships
- **Comprehensive/Technical**: Concrete examples, code snippets, real data

### Step 1: Understand Deeply
For each concept, ask: What does it DO? What relationships exist? What's the core flow?

### Step 2: Map Concepts to Patterns
| If the concept... | Use this pattern |
|-------------------|------------------|
| Spawns multiple outputs | **Fan-out** (radial arrows from center) |
| Combines inputs into one | **Convergence** (funnel, arrows merging) |
| Has hierarchy/nesting | **Tree** (lines + free-floating text) |
| Is a sequence of steps | **Timeline** (line + dots + labels) |
| Loops or improves continuously | **Spiral/Cycle** (arrow returning to start) |
| Is an abstract state or context | **Cloud** (overlapping ellipses) |
| Transforms input to output | **Assembly line** (before -> process -> after) |
| Compares two things | **Side-by-side** (parallel with contrast) |
| Separates into phases | **Gap/Break** (visual separation) |

### Step 3: Ensure Variety
Each major concept must use a different visual pattern. No uniform cards or grids.

### Step 4: Sketch the Flow
Mentally trace how the eye moves through the diagram.

### Step 5: Generate JSON
See below for how to handle large diagrams.

### Step 6: Render & Validate (MANDATORY)
Run the render-view-fix loop until the diagram looks right.

---

## Large / Comprehensive Diagram Strategy

**Build the JSON one section at a time.** Do NOT attempt to generate the entire file in a single pass.

### The Section-by-Section Workflow

**Phase 1: Build each section**
1. Create the base file with JSON wrapper and first section.
2. Add one section per edit.
3. Use descriptive string IDs (e.g., `"trigger_rect"`, `"arrow_fan_left"`).
4. Namespace seeds by section (section 1 uses 100xxx, section 2 uses 200xxx).
5. Update cross-section bindings as you go.

**Phase 2: Review the whole** — Check cross-section arrows, spacing, ID references.

**Phase 3: Render & validate** — Run the render-view-fix loop.

### What NOT to Do
- Don't generate the entire diagram in one response.
- Don't use a coding agent to generate the JSON.
- Don't write a Python generator script.

---

## Shape Meaning

| Concept Type | Shape | Why |
|--------------|-------|-----|
| Labels, descriptions | **none** (free-floating text) | Typography creates hierarchy |
| Markers on a timeline | small `ellipse` (10-20px) | Visual anchor |
| Start, trigger, input | `ellipse` | Soft, origin-like |
| End, output, result | `ellipse` | Completion |
| Decision, condition | `diamond` | Classic decision symbol |
| Process, action, step | `rectangle` | Contained action |
| Abstract state | overlapping `ellipse` | Fuzzy, cloud-like |

**Rule**: Default to no container. Aim for <30% of text elements inside containers.

---

## Color as Meaning

Every color choice must come from `references/color-palette.md`. Do not invent new colors.

---

## Modern Aesthetics

- `roughness: 0` — Default for professional diagrams
- `strokeWidth: 2` — Standard for shapes and arrows
- `opacity: 100` — Always, for all elements

---

## Layout Principles

- **Hero**: 300x150, **Primary**: 180x90, **Secondary**: 120x60, **Small**: 60x40
- Most important element has the most whitespace around it (200px+)
- Flow: left->right or top->bottom
- Every relationship needs an arrow

---

## Text Rules

**CRITICAL**: The JSON `text` property contains ONLY readable words.

Settings: `fontSize: 16`, `fontFamily: 3`, `textAlign: "center"`, `verticalAlign: "middle"`

---

## JSON Structure

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [...],
  "appState": {
    "viewBackgroundColor": "#1a1b26",
    "gridSize": 20
  },
  "files": {}
}
```

See `references/element-templates.md` for copy-paste JSON templates.

---

## Component Libraries

Pre-made icon/shape libraries are available in `references/libraries/`. Each `.excalidrawlib` file contains reusable components as standard Excalidraw element arrays.

### Available Libraries

| Library | Components | Use For |
|---------|-----------|---------|
| `aws-serverless` | Lambda, API Gateway, DynamoDB, S3, SQS, SNS, CloudFront, Cognito, EventBridge, Step Functions, etc. (24 items) | AWS architecture diagrams |
| `system-design` | Server, Load Balancer, Relational DB, Graph DB, CDN, DNS, Message Queue, Pipeline, Cloud, Mobile, Web App, etc. (24 items) | System design diagrams |
| `infra` | VPC, Public/Private Subnet, Docker, GitHub, Slack, Server, User, Device, Email (11 items) | Infrastructure & networking diagrams |
| `dev-icons` | File types (PDF, SQL, XLS), languages (Python, Java, Go, Rust, TypeScript, React, Swift), tools (Webpack, Vite, Jest) (65 items) | File/language/tool icons |
| `data-viz` | Bar, Line, Area, Scatter, Bubble, Heatmap, Treemap, Pie, Donut, Box & Whisker, Violin, etc. (32 items) | Chart type visualization |
| `data-platform` | Kafka, Spark, Databricks, dbt, Airflow, Flink, Trino, Iceberg, Delta Lake, Elasticsearch, MinIO, etc. (33 items) | Data engineering architecture |

### How to Use Library Components

1. **Read** the `.excalidrawlib` file from `references/libraries/`
2. **Find** the matching `libraryItems[]` (v2) or `library[]` (v1) entry by text label
3. **Copy** its elements array into your diagram's `elements[]`
4. **Adjust**: Offset all `x`/`y` coordinates to position the component, assign new unique `id` and `seed` values
5. **Re-color** (optional): Update `strokeColor`/`backgroundColor` to match `color-palette.md` if you want Tokyo Night consistency

### Format Notes
- **v2 format** (`libraryItems`): Each item has `{ "elements": [...] }` wrapper
- **v1 format** (`library`): Each item is a bare element array `[...]`
- Components use `groupIds` to keep their sub-elements together — preserve these relationships

---

## Render & Validate (MANDATORY)

### How to Render

```bash
cd ~/.claude/skills/excalidraw-diagram/references && uv run python render_excalidraw.py <path-to-file.excalidraw>
```

Outputs a PNG next to the `.excalidraw` file. Then use **Read tool** on the PNG to view it.

### The Loop

1. **Render & View** — Run render script, Read the PNG.
2. **Audit** — Does visual structure match conceptual design?
3. **Check defects** — Text overflow, overlapping, arrows misrouted, uneven spacing.
4. **Fix** — Edit the JSON.
5. **Re-render** — Repeat until clean. Typically 2-4 iterations.

### First-Time Setup
```bash
cd ~/.claude/skills/excalidraw-diagram/references
uv sync
uv run playwright install chromium
```

---

## Quality Checklist

### Depth & Evidence
1. Research done? 2. Evidence artifacts? 3. Multi-zoom? 4. Concrete over abstract? 5. Educational value?

### Conceptual
6. Isomorphism? 7. Argument? 8. Variety? 9. No uniform containers?

### Container Discipline
10. Minimal containers? 11. Lines as structure? 12. Typography hierarchy?

### Structural
13. Connections? 14. Flow? 15. Hierarchy?

### Technical
16. Text clean? 17. `fontFamily: 3`? 18. `roughness: 0`? 19. `opacity: 100`? 20. Container ratio <30%?

### Visual Validation
21. Rendered to PNG? 22. No text overflow? 23. No overlaps? 24. Even spacing? 25. Arrows correct? 26. Readable? 27. Balanced?
