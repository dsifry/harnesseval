# Distinct verified defects — three counts, and which one to quote

Three different units have been used in this campaign. They differ by more than 50%, so the report must
say which one is being quoted.

| unit | count | x goldens (42) | what it means |
|---|---|---|---|
| raw candidate union (§10a/b) | 359 | 8.5x | every distinct anchor/text key across runs (massively overcounted) |
| §10c verified candidates | 211 | 5.0x | after the semantic merge, before execution |
| **execution-verified bundles** | **91** | **2.17x** | bundles that failed pre-fix and passed post-fix, after duplicate removal |
| **label-level distinct defects** | **~143** | **3.40x** | the same bundles expanded by the merge audit: 28 bundles contain 2-4 distinct defects each |

## Why the bundle count is not the defect count

`tools/verified_gold_merge_audit.py` asked, per bundle, whether its findings really describe ONE defect
(judge deepseek-4.1-flash-background). It audited 100 bundles and flagged 28 as multi-concern:

| bundle | findings | distinct defects inside it |
|---|---|---|
| 4-B02 | 123 | 4 (referer as auth gate, jobs enqueued before throttle, case-sensitive host compare, …) |
| 4-B26 | 12 | 4 (mutating contents, line-anchored regex bypass, unhandled URI parse, …) |
| 11059-B05 | 91 | 4 (timing-unsafe compare, header type handling, missing rate limit, …) |
| 11059-B09 | 41 | 4 (missing method guard, unparsed body errors, missing schema validation, …) |
| 11059-B10 | 75 | 4 (unauthenticated sync endpoint, Lark envelope mismatch, …) |
| 11059-B19 | 21 | 4 (case normalization, array headers, fail-open, timing compare) |
| 11059-B23 | 8 | 4 (throw-on-parse-failure, read-modify-write race, …) |
| 10-B03 / 10-B05 / 4-B15 | — | 3 each |
| 20 further bundles | — | 2 each |

Summing the audited `n_distinct` over the 101 bundles (including the duplicates' unique labels, since the
label-level union handles overlap) gives **146 gross**, and merging the cross-bundle repeated labels
(lexical Jaccard >= 0.45) gives **~143 distinct**.

## Per PR

| PR | bundles (incl. duplicates) | gross label count | distinct (label union) |
|---|---|---|---|
| 4 | 41 | 60 | 59 |
| 8 | 6 | 7 | 7 |
| 10 | 18 | 22 | 22 |
| 10967 | 5 | 6 | 6 |
| 11059 | 15 | 32 | 30 |
| 14740 | 16 | 19 | 19 |
| **total** | **101** | **146** | **~143** |

## Uncertainty

- The split into per-bundle labels is a single judge pass, and the cross-bundle label merge is lexical.
  Synonyms that were not merged inflate the count; labels that are facets of one root cause deflate it.
- Unaudited bundles are counted as 1 each, so any multi-defect bundle among them undercounts.
- I would quote **~135-145**, i.e. **3.2-3.5x the golden set**, and cite the bundle-level **91 (2.17x)** as
  the strict floor (only bundles proven by an executed test survive that count).
