# External reviewers (CodeRabbit / BugBot) vs. our harnesses — gap analysis

**Question:** Which clusters do CodeRabbit and Cursor BugBot catch that metareview (and
Compound Engineering) never caught anywhere in the model×effort matrix, and what should we
add?

**Data.** Martian CRB vendored external-reviewer findings
(`third_party/code-review-benchmark/offline/results/anthropic_claude-opus-4-5-20251101/candidates.json`):
CodeRabbit 318 + BugBot 129 findings across the 50-PR bench; **123 on our 6 benchmark PRs**.
"Our union" = every mrv + ce pass run on those PRs (any model, any effort — low/medium/high/
xhigh), all findings regardless of verdict, plus golden-matched candidates: 2.0k–6.3k
findings per PR. Each external finding was matched against the top-40 TF-IDF-retrieved union
findings by parallel subagent semantic matching (`analysis/ext_match_results_*.json`).

## Results

| | |
|---|---:|
| External findings (CodeRabbit + BugBot, 6 PRs) | 123 |
| Caught by our harnesses somewhere in the matrix | **113 (92%)** |
| **Never caught by either harness** | **10 (8%)** |

**Cross-validation (the more interesting direction):** of the 73 external findings Martian's
golden-based eval labels "unmatched" (i.e. counted as FPs in their precision metric), our
adjudicated runs **confirm 28 as real bugs** (17 via ce, 11 via mrv) — destroyRecord without
`.catch`, `force: true` on shipped migrations, non-atomic setnx/expire, missing fetch timeout,
TLD regex caps, unescaped SQL backfill, usernames not normalized, pagination params unclamped,
Zod default key-stripping dropping `expires_in`, header-array handling. These land almost
one-for-one on the CE-only clusters from `CE_VS_MRV_GAPS.md` — two independent instruments
(CodeRabbit/BugBot and CE) finding the same residue MRV misses.

## The 10 misses, clustered

### A. Interface-contract siblings across ALL implementers (real, actionable)
- PR10967 CodeRabbit: Office365CalendarService `updateEvent`/`deleteEvent` don't match the
  `Calendar` interface (missing `externalCalendarId` / `event` params) — they always hit the
  default calendar path. This is the **sibling of a golden we did catch** ("Calendar interface
  now requires createEvent(event, credentialId), but some implementations still declare
  createEvent(event) only"). We caught the `createEvent` variant and missed the
  `updateEvent`/`deleteEvent` variants.

### B. Config/flag propagation on touched paths (real)
- PR14740 CodeRabbit: `sendAddGuestsEmails` can leak hidden notes by not respecting
  `hideCalendarNotes` — sibling of the `disableStandardEmails` golden we caught. Same
  pattern: a notification path gated by several user-config flags; we checked one flag, not
  the family.

### C. Transformation field-fidelity in import paths (real)
- PR4 CodeRabbit: disqus importer sets `raw` and `cooked` both to `p[:cooked]` — `raw` should
  be source text, not HTML.
- PR4 CodeRabbit: `Date.parse` loses time information (should be `DateTime.parse`).

### D. Template/test-infrastructure defects (minor but real)
- PR8 CodeRabbit: stray closing `</div>` in `group/members.hbs`.
- PR10 CodeRabbit: `Fabricator(:private_category)` `after_build` uses `update!` (persists on
  `Fabricate.build`) and `transients[:group].id` raises if group not passed.

### E. Style/hygiene (deliberately suppressed — not a gap)
- `be_true` → `be true` deprecation; RuboCop blank-lines; `image_tag` suggestion;
  MultiEmail duplicates an existing component. Metareview's rubric explicitly suppresses
  style nits; counting these would trade precision for nothing.

## What to add (deltas to the existing recommendation set)

The misses **reinforce the existing plan rather than demanding new lenses**:

1. **API-contract enhancement gets one more hunt pattern** (Architecture brief,
   `API-CONTRACT-BREAKING-CHANGES`): *"when a diff changes an interface/abstract-method
   signature, check EVERY implementer, not just the call sites in the diff"* — we caught the
   `createEvent` golden but missed `updateEvent`/`deleteEvent` in the same file family.
2. **Completeness brief: sibling-flag propagation.** *"When a diff touches a
   notification/rendering/serialization path, enumerate ALL user-config flags that gate that
   path (disable*, hide*, include*) and check each one"* — caught `disableStandardEmails`,
   missed `hideCalendarNotes`.
3. **Format-drift/Data-migration brief: transformation field-fidelity.** *"On
   import/export/migration paths, each output field must derive from the right source with
   the right precision (raw vs cooked, date vs datetime, precision loss on parse)."*
4. Testing-quality: stray-tag/template validity and fabricator build-vs-create semantics are
   already in scope conceptually; not worth a dedicated pattern.
5. **Do NOT add style/deprecation/dedup checks** — the 5 style misses are our precision
   discipline working as designed.

## Caveats

- Retrieval was top-40 lexical + one semantic pass; a same-issue phrased very differently
  and ranked below 40 could produce a false "miss" — but with 2k–6k union findings per PR and
  92% coverage, the residual risk is small.
- The union includes *all* models and efforts, so "we caught it" means "our best cell caught
  it," not "a typical cell catches it" — the per-cell (e.g. GLM-low) coverage is lower.
- Martian's "FP" label on external findings means golden-unmatched, not false — 28/73
  confirmed real by our adjudication, so external-tool precision is systematically
  underestimated by golden-only metrics (consistent with the hidden-gold thesis of report2).
