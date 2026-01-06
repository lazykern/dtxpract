Autoplay and ghost logic

Autoplay
- Autoplay is per-lane (bIsAutoPlay array) and can be fully enabled per instrument.
- In judgement and scoring paths, auto hits can skip input adjust and may be penalized in score.
- Some scoring paths are gated by ConfigIni.bAutoAddGage (if false, auto hits do not add score).
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs and CActPerfCommonScore.cs.

Target ghost evaluation
- If target ghost data is enabled, each chip is evaluated using a stored lag value:
  - ghostLag is read per chip index from listTargetGhsotLag.
  - judgement is computed at (chip.nPlaybackTimeMs + ghostLag) with saveLag=false.
  - counts and max combo are updated for the ghost.
- A high bit in ghostLag resets combo (used for bad hit reconstruction).
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (tUpdateAndDraw_Chips).

Ghost lag storage
- When a chip is judged, the lag is stored on the chip (pChip.nLag).
- This is used for ghost playback or post-analysis.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (e指定時刻からChipのJUDGE).

Key code references
- DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs: ghost handling, lag storage
- DTXMania/Code/Stage/07.Performance/CActPerfCommonScore.cs: auto penalties
