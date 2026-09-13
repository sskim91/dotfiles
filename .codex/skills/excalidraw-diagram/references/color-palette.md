# Color Palette & Brand Style — Tokyo Night

**This is the single source of truth for all colors and brand-specific styles.** To customize diagrams for your own brand, edit this file — everything else in the skill is universal.

---

## Shape Colors (Semantic)

Colors encode meaning, not decoration. Each semantic purpose has a fill/stroke pair.
Based on [Tokyo Night](https://github.com/enkia/tokyo-night-vscode-theme) color scheme.

| Semantic Purpose | Fill | Stroke |
|------------------|------|--------|
| Primary/Neutral | `#7aa2f7` | `#3b4261` |
| Secondary | `#7dcfff` | `#3b4261` |
| Tertiary | `#b4f9f8` | `#3b4261` |
| Start/Trigger | `#e0af68` | `#8c6c3e` |
| End/Success | `#9ece6a` | `#5a7a3a` |
| Warning/Reset | `#f7768e` | `#914255` |
| Decision | `#ff9e64` | `#8c5a3a` |
| AI/LLM | `#bb9af7` | `#6a4db5` |
| Inactive/Disabled | `#565f89` | `#3b4261` (use dashed stroke) |
| Error | `#f7768e` | `#8b3d54` |

**Rule**: Always pair a darker stroke with a lighter fill for contrast.

---

## Text Colors (Hierarchy)

Use color on free-floating text to create visual hierarchy without containers.

| Level | Color | Use For |
|-------|-------|---------|
| Title | `#c0caf5` | Section headings, major labels |
| Subtitle | `#7aa2f7` | Subheadings, secondary labels |
| Body/Detail | `#565f89` | Descriptions, annotations, metadata |
| On dark fills | `#c0caf5` | Text inside dark-colored shapes |
| On light fills | `#1a1b26` | Text inside light-colored shapes |

---

## Evidence Artifact Colors

Used for code snippets, data examples, and other concrete evidence inside technical diagrams.

| Artifact | Background | Text Color |
|----------|-----------|------------|
| Code snippet | `#1a1b26` | Syntax-colored (use Tokyo Night token colors below) |
| JSON/data example | `#1a1b26` | `#9ece6a` (green) |

### Tokyo Night Syntax Token Colors

| Token | Color |
|-------|-------|
| Keyword | `#bb9af7` (purple) |
| String | `#9ece6a` (green) |
| Function | `#7aa2f7` (blue) |
| Number | `#ff9e64` (orange) |
| Comment | `#565f89` (gray) |
| Type | `#7dcfff` (cyan) |
| Variable | `#c0caf5` (foreground) |

---

## Default Stroke & Line Colors

| Element | Color |
|---------|-------|
| Arrows | Use the stroke color of the source element's semantic purpose |
| Structural lines (dividers, trees, timelines) | `#3b4261` (dark border) or `#565f89` (comment gray) |
| Marker dots (fill + stroke) | `#7aa2f7` (primary blue) |

---

## Background

| Property | Value |
|----------|-------|
| Canvas background | `#1a1b26` (Tokyo Night storm) |

---

## Reference: Full Tokyo Night Palette

| Name | Hex | Role |
|------|-----|------|
| bg (storm) | `#1a1b26` | Canvas background |
| bg (night) | `#24283b` | Elevated surfaces |
| border | `#3b4261` | Strokes, borders |
| comment | `#565f89` | Subtle text, disabled |
| fg | `#c0caf5` | Primary text |
| blue | `#7aa2f7` | Primary accent |
| cyan | `#7dcfff` | Secondary accent |
| teal | `#b4f9f8` | Tertiary accent |
| green | `#9ece6a` | Success, strings |
| yellow | `#e0af68` | Warnings, triggers |
| orange | `#ff9e64` | Decisions, numbers |
| red | `#f7768e` | Errors, warnings |
| magenta | `#bb9af7` | AI/LLM, keywords |
