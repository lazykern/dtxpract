Scoring and combo rules

Combo
- Combo increments on Perfect/Great/Good, resets on Poor/Miss/Bad.
- Stored per-instrument in actCombo.nCurrentCombo.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs (tProcessChipHit).

Skill modes and score formulas
- ConfigIni.nSkillMode controls scoring logic:
  - 0 = Classic scoring
  - 1 = XG scoring
- Scoring is applied in tProcessChipHit after judgement.

Classic scoring (nSkillMode == 0)
- Score delta uses a combo multiplier with per-judgement base values:
  - nComboScoreDelta = {350, 200, 50, 0} for Perfect, Great, Good, Poor/Miss.
  - If combo <= 500, delta = base * combo.
  - For Perfect and combo > 500, base * 500.
- Auto add behavior:
  - If bAutoAddGage is false, only non-auto hits add score.
  - If true, auto hits can add score.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs.

XG scoring (nSkillMode == 1)
- Uses a "1,000,000 max" scheme with a base unit computed from note count.
- Perfect base:
  - drums: (1,000,000 - 500 * bonusCount) / (1275 + 50 * (maxCombo - 50))
  - guitar/bass: 1,000,000 / (1275 + 50 * (maxCombo - 50))
- Great = 0.5 * base, Good = 0.2 * base.
- Combo multiplier:
  - combo < 50: base * combo
  - combo >= 50: base * 50 (unless last note)
- Long note bonus is accumulated separately and added when long notes end (guitar/bass).
- Auto add behavior (bAutoAddGage) controls whether auto hits add score; otherwise only non-auto adds.
- See DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs.

Auto-play penalties
- CActPerfCommonScore.Add applies penalties when auto play is enabled:
  - Guitar/Bass auto pick and auto neck reduce score (divides by 2 for each).
  - If all-auto and AutoAddGage is off, score delta becomes 0.
- See DTXMania/Code/Stage/07.Performance/CActPerfCommonScore.cs.

Key code references
- DTXMania/Code/Stage/07.Performance/CStagePerfCommonScreen.cs: scoring in tProcessChipHit
- DTXMania/Code/Stage/07.Performance/CActPerfCommonScore.cs: Add (auto penalties)
