Gauge and stage failure

Gauge delta table
- Gauge changes are driven by fDamageGaugeDelta[judgement, part].
- Default values (drums/guitar/bass) per judgement index:
  - Perfect: 0.004 / 0.006 / 0.006
  - Great:   0.002 / 0.003 / 0.003
  - Good:    0.000 / 0.000 / 0.000
  - Poor:   -0.020 / -0.030 / -0.030
  - Miss:   -0.050 / -0.050 / -0.050
- In XG mode, drums use a different tuning for Perfect/Great/Poor/Miss.
- See DTXMania/Code/Stage/07.Performance/CActPerfCommonGauge.cs.

Risky and hazard
- Risky mode reduces gauge on Miss/Poor by a fixed amount and decrements a counter.
- Hazard mode makes Great/Good behave like Miss (full negative damage).
- Damage level multiplier applies to Miss when not in risky mode.
- See CActPerfCommonGauge.Damage.

Stage failure trigger
- If STAGEFAILED is enabled and not in training mode, the stage fails when gauge is empty.
- The drum screen checks actGauge.IsFailed and triggers stage failure state, stopping all chip sounds.
- See DTXMania/Code/Stage/07.Performance/DrumsScreen/CStagePerfDrumsScreen.cs and CActPerfStageFailure.cs.

Key code references
- DTXMania/Code/Stage/07.Performance/CActPerfCommonGauge.cs: Damage
- DTXMania/Code/Stage/07.Performance/DrumsScreen/CStagePerfDrumsScreen.cs: failure check
- DTXMania/Code/Stage/07.Performance/CActPerfStageFailure.cs: failure animation/sound
