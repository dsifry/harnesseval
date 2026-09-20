> **SUPERSEDED (2026-09-18) — kept as the audit record of that stage.** The totals below (103 defects /
> 145 gold) predate the under-count recovery and the container-test normalisation. **Current: 42 goldens +
> 110 individually test-validated defects = 152** (`GOLD_DEFECT_CATALOG.md`, `DEFECT_REGISTRY.json` `_final`).

# Label ↔ test reconciliation — 2026-09-18

The registry labels were inherited from an LLM merge audit (`MERGE_AUDIT.json`), so a label can describe
something other than what the defect's own test demonstrated. The catalogue flags every defect whose
declared claim does not resemble its label (19). Each was re-adjudicated by reading **the test's own
assertions and the fix's hunks** — never the label against another label.

## Relabelled (the test is authoritative)

| defect | old (inherited) label | corrected label | evidence |
|---|---|---|---|
| `10-D03` | "missing controller test coverage for mutating endpoints and fallbacks" | **Blank/nil `host` crashes `before_validation` on a mutating (create/update) embeddable-host request** | its test asserts normalization, lookup, and that a nil host does not raise on the mutating path. "Test coverage" is not a behaviour defect |
| `11059-D09` | "unhandled schema/decryption/JSON parse errors" | **Handler does not restrict the HTTP method and lets malformed input raise an unhandled ZodError (should answer 405/400)** | the test asserts `GET → 405` and malformed body `→ 400`, not a 500 from an escaped ZodError |

## Two duplicates the six reviewers missed (found by fix-location evidence)

The reviewers compared labels; the decisive evidence is **which lines the defect's own fix patches**.

| merged | into | evidence |
|---|---|---|
| `11059-D13` | `11059-D14` | both fixes change the *same line* — `return response;` in `refreshOAuthTokens.ts` — the credential-sync branch returning the raw fetch `Response`. D13 → `response.json()`, D14 → a merged token object: two minimal fixes, one defect. (`D15`, Webex, had already been merged here) |
| `11059-D23` | `11059-D22` | both concern the *same throw site*, `parseRefreshTokenResponse.ts:20-23` (`if (!refreshTokenResponse.success) throw`). D22 = "do not throw, return a structured failure"; D23 = "throw `HttpError(400)` instead of a generic `Error`". One behavioural decision at one line, so one defect; the bundle's own test asserts D22's prescription |

## Confirmed consistent (flags cleared)

`10-D04`, `10967-D05`, `11059-D03`, `11059-D10`, `11059-D12`, `11059-D17`, `11059-D21`, `4-D16`,
`4-D26`, `4-D29`, `10-D07`, `4-D30`, `14740-D03`, `14740-D12`, `14740-D02` — the test asserts the labelled
claim. `4-D29` is worth noting: its test asserts the labelled mutation claim **and** an unlabelled second
claim (a degenerate `http://` reaching `URI()`); the unlabelled half is tracked as an under-count item, not
a label error.

## Result

| | before | after |
|---|---|---|
| defects | 106 | **103** |
| total gold (42 + defects) | 148 (3.52×) | **145 (3.45×)** |
| via this pass | — | −2 duplicate, 2 relabelled, 15 flags cleared |
