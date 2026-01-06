Input handling and judgement

Judgement windows
- e指定時刻からChipのJUDGE computes lag = (hitTime + inputAdjust) - chip.nPlaybackTimeMs.
- Absolute lag is compared to STHitRanges (Perfect/Great/Good/Poor/Miss). Default ranges are in milliseconds:
  - Perfect: 34, Great: 67, Good: 84, Poor: 117.
- Drum pedals (BD/LP/LBD) use a separate hit range (stDrumPedalHitRanges).
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (e指定時刻からChipのJUDGE) and DTXMania/Code/App/STHitRanges.cs.

Input timing adjustment
- Per-instrument input adjust (ConfigIni.nInputAdjustTimeMs) is added to hit time.
- Auto-play skips input adjust (uses 0).

Drum hit flow (example)
- CStagePerfDrumsScreen routes pad input to the nearest candidate chip and calls tProcessDrumHit.
- tProcessDrumHit:
  - determines lane/pad from channel,
  - computes judgement,
  - ignores Miss,
  - calls tProcessChipHit for scoring/gauge/combo,
  - triggers lane flush, pad animation, and chip fire effects,
  - plays sound (chip or pad priority).
- See DTXMania/Code/Stage/07.Performance/DrumsScreen/CStagePerfDrumsScreen.cs (tProcessDrumHit).

Drum hit sound priority
- For HH/FT/CY/LP groups, ConfigIni.eHitSoundPriority* selects whether chip sound or pad sound wins when both exist.
- The chosen chip may be substituted (e.g., HH open -> HH close if HHO chips are absent).

Drum input routing flow (DTXMania drums)
- For each pad input event:
  1) Determine input adjust time (0 if lane is auto-play).
  2) Resolve candidate chips for that pad group (HH/HHO/LC, CY/RD, LT/FT, BD/LP/LBD, etc.).
  3) Compute judgement for each candidate (e指定時刻からChipのJUDGE).
  4) Prefer non-Miss candidates; when multiple candidates exist, choose by time order or configured group rules.
  5) Call tProcessDrumHit on the selected chip (or no-op if all Miss).
  6) Optionally play empty-hit sound if no chip and empty-hit is enabled.
- This logic lives in CStagePerfDrumsScreen.tHandleKeyInput with many per-pad branches.

Drum pad grouping and fallback behavior
- Hi-hat group: HH/HHO/LC are routed together depending on HH group config and chip availability.
  - If no HHO chips exist, HHO input falls back to HH; if no LC chips exist, LC may fall back to HH.
- Cymbal group: CY and RD are treated as a group when CYGroup is common; RD falls back to CY if no RD chips exist.
- Tom group: LT/FT can be grouped if FTGroup is common.
- Pedal group: BD/LP/LBD inputs can resolve to the nearest matching pedal chip (including combinations).
- These rules are in the per-pad input routing inside tHandleKeyInput (drums screen).

Drum pad mapping (channel -> pad)
- eChannelToPad mapping for drums is defined in CStagePerfDrumsScreen:
  - HH, SD, BD, HT, LT, CY, FT, HHO, RD, (unused), (unused), LC.
- This mapping is used to resolve lane indices and pad effects.

Correct-lane enforcement
- tProcessChipHit receives bCorrectLane; if false, judgement is forced to Miss.
- This is used for some gameplay cases (e.g., ghost/autoplay scenarios).

Key code references
- DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs: e指定時刻からChipのJUDGE, tProcessChipHit
- DTXMania/Code/Stage/07.Performance/DrumsScreen/CStagePerfDrumsScreen.cs: tProcessDrumHit
- DTXMania/Code/App/STHitRanges.cs: judgement ranges
