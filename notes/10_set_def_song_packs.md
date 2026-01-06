Song pack format: set.def

Purpose
- set.def groups multiple difficulty charts (L1-L5) under a single song entry.
- Used by song selection to display multiple difficulties.

Syntax
- #TITLE: song title
- #FONTCOLOR: hex color (e.g., FFCC00)
- #L1LABEL..#L5LABEL: labels (Novice/Basic/etc)
- #L1FILE..#L5FILE: chart file names
- Multiple blocks can be stacked; a new #TITLE starts a new block.

Parsing rules
- Files are read as Shift-JIS.
- Lines starting with ';' are comments. Inline ';' comments are stripped.
- If a block has FILE without LABEL, default labels are filled.
- If LABEL exists without FILE, it is discarded.
- See DTXMania/Code/Score,Song/CSetDef.cs.

Example
- /home/lazykern/lab/dtxprac/examples/dtx/396 - Goodbye -album version-/set.def

Key code references
- DTXMania/Code/Score,Song/CSetDef.cs
