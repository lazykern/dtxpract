Long notes and wailing

Long note pairing (load time)
- Long notes exist for guitar/bass via channels EChannel.Guitar_LongNote and EChannel.Bass_LongNote.
- During chart load, the parser finds a start chip and pairs it with a later LongNote channel chip at the same lane/time rules.
- The start chip stores chipロングノート終端 and is marked as a long note.
- See DTXMania/Code/Score,Song/CDTX.cs ("Long Note Processing" in the load loop).

Long note state (runtime)
- When a long note start is hit:
  - pChip.bロングノートHit中 = true
  - chipロングノートHit中[inst] is set
  - duration is stored (endTime - startTime)
- The end chip clears the state when hit or when judged as miss.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs.

Long note bonus scoring (XG)
- While a long note is held, the system splits its duration into 6 parts.
- Each part crossing adds 100 bonus score; accumulated bonus is added at completion.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (nAccumulatedLongNoteBonusScore).

Long note rendering
- When a long note is active, the renderer draws a tail between start and end distances.
- The tail length is derived from (endDistance - startDistance).
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (chip drawing for long notes).

Wailing (guitar/bass)
- Wailing channels exist (EChannel.Guitar_Wailing, EChannel.Bass_Wailing).
- Wailing chips are treated as special visible chips and have separate rendering and scoring paths.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (wailing draw and chip handlers).

Key code references
- DTXMania/Code/Score,Song/CDTX.cs: long note pairing
- DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs: long note state/bonus/rendering
- DTXMania/Code/Score,Song/EChannel.cs: long note and wailing channels
