Audio playback and mixer behavior

WAV definitions
- #WAVxx defines a CWAV entry with filename, volume, pan, and size.
- VOLUME/PAN/SIZE commands can appear before #WAVxx; the loader patches CWAV entries when definitions appear.
- See DTXMania/Code/Score,Song/CDTX.cs (t入力_行解析_WAV, t入力_行解析_WAVVOL_VOLUME, t入力_行解析_WAVPAN_PAN, t入力_行解析_SIZE).

Chip sound playback
- On hit, tPlaySound is invoked with the resolved chip (or substituted chip for pad priority).
- BGM channel (01) triggers playback when distance < 0 if BGM is enabled.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (tUpdateAndDraw_Chips) and Drums screen tProcessDrumHit.

Mixer add/remove
- CStagePerfCommonScreen queues mixer add/remove operations to avoid too many calls per frame.
- ManageMixerQueue processes up to 2 add/remove operations every 7ms.
- Mixer is used for overlapping chip playback and for keeping long sounds alive.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (ManageMixerQueue).

Key code references
- DTXMania/Code/Score,Song/CDTX.cs: WAV parsing
- DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs: mixer queue
- DTXMania/Code/Stage/07.Performance/DrumsScreen/CStagePerfDrumsScreen.cs: tProcessDrumHit sound priority
