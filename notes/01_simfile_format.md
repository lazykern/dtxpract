DTX simfile format and parsing (DTX/GDA/G2D/BMS/BME)

Scope
- DTXMania parses simfiles in CDTX.tRead -> tRead_FromString -> t入力_行解析.
- The main chart file is .dtx/.gda/.g2d/.bms/.bme. The .ogg/.wav files are audio assets, not charts.
- Example: /home/lazykern/lab/dtxprac/examples/dtx/396 - Goodbye -album version-/goodbye-mas.dtx is a chart. The file named "キアロスクーロ (No Drums).ogg" is just audio; the chart is /home/lazykern/lab/dtxprac/examples/dtx/022 Kiarosukuuro/mstr.dtx.

File encoding
- CDTX reads files with Shift-JIS: StreamReader(..., Encoding.GetEncoding("shift-jis")).
- Some example charts are UTF-16LE (goodbye-mas.dtx). DTXMania likely relies on Shift-JIS and may misread UTF-16 unless converted. For an emulator, detect BOM and decode UTF-16/UTF-8 as needed, then normalize to internal UTF-16 string.
- Parser normalizes input: tabs -> space, Windows newlines -> \n, and appends a trailing \n.

Line grammar
- Lines are processed only if they start with '#'.
- Commands are split into:
  - command token (string after '#'),
  - parameter token (after ':', trimmed),
  - optional comment (after ';').
- Commands are case-insensitive.
- IF/ENDIF and RANDOM are supported. IF blocks can be nested; unmatched ENDIF is warned.

Header commands (examples)
- Metadata: TITLE, ARTIST, COMMENT, GENRE, PREVIEW, PREIMAGE, PREMOVIE, STAGEFILE.
- Difficulty: DLEVEL (drums), GLEVEL (guitar), BLEVEL (bass). Values >= 100 use decimal split into LEVEL/LEVELDEC.
- BPM: BASEBPM, BPM (or BPMxx), and in-chart BPM changes via channel 03 or 08 (BPMEx).
- Audio: WAVxx definitions, plus VOLUMExx and PANxx for audio parameters.
- Video/BGA: AVIxx/VIDEOxx, BMPxx/BMPTEXxx/BGA/AVIPAN/BGAPAN.
- Result: RESULTIMAGE/RESULTMOVIE/RESULTSOUND (per rank).
- Others: PANEL, MIDIFILE, MIDINOTE, BACKGROUND, BACKGROUND_GR, WALL, SOUND_*.

Object placement lines: #MMMCC: <data>
- Exactly 5 chars after '#':
  - MMM = 3-digit measure number (000-999).
  - CC = 2-digit channel (hex for DTX/BMS; mapped for GDA/G2D).
- Parser increments measure number by 1: n小節番号++ (it inserts a leading empty measure).
- Bar length channel (02) is special: parameter is a decimal multiplier (not object list).
- For all other channels, the parameter is an object list:
  - It is a string of base36 pairs, with '_' ignored.
  - Odd length is truncated by one character.
  - Each pair = one object; "00" means no chip.
  - For channel 03 (BPM), the object pairs are hex; other channels are base36.
- Each object is placed at:
  - nPlaybackPosition = (measure * 384) + (384 * i / objectCount)
  - where i is the object index within the list.

Channel to lane mapping
- Channels are enumerated in EChannel. Examples:
  - 0x11-0x1C = drum lanes (HH, SD, BD, HT, LT, CY, FT, HHO, RD, LC, LP, LBD)
  - 0x31-0x3C = drum hidden lanes (same ordering as drums; used for hidden chip variants)
  - 0xB1-0xBE = drum \"no chip\" lanes (used to suppress chip display / empty hit sounds)
  - 0x20+ = guitar lanes, 0xA0+ = bass lanes (many chord variants)
  - 0x50 = BarLine, 0x51 = BeatLine, 0x53 = FillIn
  - 0x01 = BGM, 0x02 = BarLength, 0x03 = BPM, 0x08 = BPMEx
  - 0x54/0x5A = Movie, 0x04/0x07/0x55.. = BGA layers
- See DTXMania/Code/Score,Song/EChannel.cs.

Drum channel map (DTX)
Active drums (0x11-0x1C)
- 0x11 HiHatClose (HH)
- 0x12 Snare (SD)
- 0x13 BassDrum (BD)
- 0x14 HighTom (HT)
- 0x15 LowTom (LT)
- 0x16 Cymbal (CY)
- 0x17 FloorTom (FT)
- 0x18 HiHatOpen (HHO)
- 0x19 RideCymbal (RD)
- 0x1A LeftCymbal (LC)
- 0x1B LeftPedal (LP)
- 0x1C LeftBassDrum (LBD)

Hidden drums (0x31-0x3C)
- 0x31 HiHatClose_Hidden
- 0x32 Snare_Hidden
- 0x33 BassDrum_Hidden
- 0x34 HighTom_Hidden
- 0x35 LowTom_Hidden
- 0x36 Cymbal_Hidden
- 0x37 FloorTom_Hidden
- 0x38 HiHatOpen_Hidden
- 0x39 RideCymbal_Hidden
- 0x3A LeftCymbal_Hidden
- 0x3B LeftPedal_Hidden
- 0x3C LeftBassDrum_Hidden

No-chip drums (0xB1-0xBE)
- 0xB1 HiHatClose_NoChip
- 0xB2 Snare_NoChip
- 0xB3 BassDrum_NoChip
- 0xB4 HighTom_NoChip
- 0xB5 LowTom_NoChip
- 0xB6 Cymbal_NoChip
- 0xB7 FloorTom_NoChip
- 0xB8 HiHatOpen_NoChip
- 0xB9 RideCymbal_NoChip
- 0xBC LeftCymbal_NoChip
- 0xBD LeftPedal_NoChip
- 0xBE LeftBassDrum_NoChip
- 0xBA Guitar_NoChip, 0xBB Bass_NoChip (not drums, listed for completeness)

Fill-in channel (0x53)
- Fill-in on/off chips are nudged in time to ensure order:
  - value 1 (ON) is shifted earlier by 32 ticks.
  - value 2 (OFF) is shifted later by 32 ticks.
- See CDTX.tInput_LineAnalysis_ChipLocation.

"Infinite" definition tables (WAV/BPM/VOL/PAN/SIZE)
- The parser allows object references to appear before #WAVxx or #BPMxx definitions.
- It stores temporary negative IDs (e.g., -zz) and retroactively patches chips when definitions appear.
- Arrays: n無限管理WAV/BPM/VOL/PAN/SIZE track current definition for each base36 index.
- See t入力_行解析_WAV and t入力_行解析_BPM_BPMzz.

Set.def song packs
- set.def defines multi-difficulty packs with #LxLABEL and #LxFILE.
- Parsed by CSetDef.t読み込み. See /home/lazykern/lab/dtxprac/examples/dtx/396 - Goodbye -album version-/set.def and DTXMania/Code/Score,Song/CSetDef.cs.

Key code references
- DTX reading: DTXMania/Code/Score,Song/CDTX.cs (tRead, tRead_FromString)
- Line parsing: DTXMania/Code/Score,Song/CDTX.cs (t入力_行解析, tInput_LineAnalysis_ChipLocation)
- Channel enum: DTXMania/Code/Score,Song/EChannel.cs
- Example set.def: /home/lazykern/lab/dtxprac/examples/dtx/396 - Goodbye -album version-/set.def
