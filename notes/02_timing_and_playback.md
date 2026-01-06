Timing, BPM, and playback time computation

Core timing flow
- Charts are parsed into CChip entries with nPlaybackPosition measured in ticks (384 ticks per measure).
- During load, CDTX computes nPlaybackTimeMs for every chip based on current BPM and bar length.
- The game uses CSoundManager.rcPerformanceTimer as the runtime clock for judging and rendering.

Playback time calculation
- For each chip, CDTX.tComputeChipPlayTimeMs is used:
  - timeMs = startTimePosition + (0x271 * positionDelta * barLength / bpm)
  - 0x271 is 625 decimal.
- After computing, nPlaybackTimeMs is stored via tConvertFromDoubleToIntBasedOnComputeMode.
- ConfigIni.nChipPlayTimeComputeMode controls rounding:
  - 0: floor/truncate (legacy behavior)
  - 1: high precision with Math.Round
- See DTXMania/Code/Score,Song/CDTX.cs (tComputeChipPlayTimeMs, tConvertFromDoubleToIntBasedOnComputeMode).

BPM control
- BASEBPM sets the base for BPMEx (channel 08) and some BPM logic.
- #BPM and #BPMxx define BPM values in a dictionary (CBPM). #BPM with no suffix is treated as "00".
- Channel 03 chips (BPM) encode BPM as hex values; channel 08 (BPMEx) references #BPMxx definitions.
- At runtime, when a BPM chip is hit (distance < 0), the active BPM is updated and used for UI counters.
- See DTXMania/Code/Score,Song/CDTX.cs (t入力_行解析_BPM_BPMzz) and DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (BPM handling in tUpdateAndDraw_Chips).

Bar length changes
- Channel 02 sets bar length multipliers (float), stored as a CChip with db実数値.
- During playback time computation, bar length changes update the conversion for subsequent chips.
- See DTXMania/Code/Score,Song/CDTX.cs (tInput_LineAnalysis_ChipLocation and "発声時刻の計算").

BGM adjustment
- tRead supports nBGMAdjust, which shifts nPlaybackTimeMs for all chips by a constant offset.
- See DTXMania/Code/Score,Song/CDTX.cs (nBGMAdjust handling).

Key code references
- DTXMania/Code/Score,Song/CDTX.cs: "発声時刻の計算", tComputeChipPlayTimeMs
- DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs: BPM update on hit
