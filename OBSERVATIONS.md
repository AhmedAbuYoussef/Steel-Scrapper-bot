# OBSERVATIONS.md — Things noticed, not acted on

`CLAUDE.md` requires Claude Code to write here whenever it spots something outside the current scope (a refactor opportunity, an inconsistency, a probable bug in unrelated code, a potential improvement). The point is: **don't lose the observation, but also don't act on it without B's say-so.**

B reviews this file periodically and decides which observations become tasks (move them to the spec or to the next step's brief), which get archived, and which get killed.

---

## Open observations

Most recent at top.

### 2026-04-30 — `cbe_metrics` row-count discrepancy: 60 rows seeded, Appendix B says "12"

- **What I noticed:** Appendix B's "Not in Step 1" note says "Hand-type 12 dummy `cbe_metrics` rows," but spec §4 (`"last 12 months"`), §8 (5 locked metrics), and §11 prompt 5 ("trend over past 12 months") all require 12 monthly values **per metric**. 12 rows total cannot satisfy criterion #6 for prompt 5.
- **Where:** `db.py` seed for `cbe_metrics` table; spec Appendix B + §11.
- **Why it might matter:** If B reads Appendix B as a hard 12-row cap, prompt 5 cannot meet criterion #6 with the current data. If 60 rows is correct, Appendix B should be edited in v1.3 of the spec to say "12 months × 5 metrics = 60 rows."
- **What I did:** Seeded 60 rows (12 months × 5 metrics, window 2025-04 → 2026-03, plausible monotonic series) and explicitly flagged the deviation in the Step A handoff for B's sign-off.
- **Awaiting:** B's call — keep 60, or truncate to 12.

### 2026-04-30 — `cleaning_log.rows_affected` column type loses cells-vs-rows nuance

- **What I noticed:** Spec §6 lists "312 cells" for one of the cleaning issues, but `cleaning_log.rows_affected` is an INTEGER column — the cells-vs-rows distinction is lost when stored as `312`.
- **Where:** `db.py` schema for `cleaning_log`; spec §6.
- **Why it might matter:** For the demo this is acceptable (it's dummy data), but if a future version reuses this schema for real cleaning runs, the unit ambiguity could cause silent reporting errors.
- **Why I didn't act:** Out of scope for Step A; flagged for Step B or later.

---

## Resolved / archived

(None yet.)
