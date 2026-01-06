Chip lifecycle and rendering loop

Data structures
- CDTX.listChip holds all chips, sorted by nPlaybackPosition (CChip.CompareTo).
- CStagePerfCommonScreen keeps nCurrentTopChip as the active index into listChip.
- Each CChip stores timing (nPlaybackTimeMs), position (nPlaybackPosition), lane (nChannelNumber), and per-part distance from the judgement line (nDistanceFromBar).

Distance from bar (scroll position)
- Each frame, CChip.ComputeDistanceFromBar converts (nPlaybackTimeMs - currentTime) to a pixel distance using scroll speed.
- Separate speeds per instrument (drums/guitar/bass) are applied.
- Long notes compute distance for end chips too.
- See DTXMania/Code/Score,Song/CChip.cs (ComputeDistanceFromBar).

Update/draw flow
- CStagePerfCommonScreen.tUpdateAndDraw_Chips iterates listChip from nCurrentTopChip and:
  - updates distance for each chip,
  - early-exits when chips are far enough away (distance > 600),
  - advances nCurrentTopChip when chips move past the bar and are already hit.
- The method dispatches per-channel drawing and behavior (drums, guitar/bass, BGM, BGA, BPM, etc.).
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (tUpdateAndDraw_Chips).

Drums fill-in handling
- Fill-in sections are driven by channel 0x53 chips with values 1 (on) and 2 (off).
- Drum screen checks whether the current chip is the last within a fill-in window; this affects chip fire effects.
- See DTXMania/Code/Stage/07.Performance/DrumsScreen/CStagePerfDrumsScreen.cs (bフィルイン区間の最後のChipである).

Auto-miss behavior
- If a visible chip passes the judgement line without being hit, the system auto-processes it as a miss:
  - For each chip, if distance < 0 and e指定時刻からChipのJUDGE returns Miss, tProcessChipHit is called.
- This triggers combo break, gauge damage, and result counters.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (tUpdateAndDraw_Chips, e指定時刻からChipのJUDGE).

Chip ordering
- CChip.CompareTo orders by nPlaybackPosition, then by channel priority table so overlapping chips draw correctly.
- See DTXMania/Code/Score,Song/CChip.cs (CompareTo).

Key code references
- DTXMania/Code/Score,Song/CChip.cs: CompareTo, ComputeDistanceFromBar
- DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs: tUpdateAndDraw_Chips
