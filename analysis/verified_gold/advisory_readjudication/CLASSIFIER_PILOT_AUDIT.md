# Common advisory classifier: bounded pilot audit

Status: seven bounded classifier probes complete. The source-review sections below were written before reading their respective classifier outputs; results are appended separately.

## Selection and limits

The five largest groups from the second 60-finding grouping pilot for Discourse PR 10 were selected for a qualitative check. This is a purposive sample from one PR, not a random sample, an accuracy estimate, or human validation of the full advisory set. Grouping uses clipped text; classification receives the complete representative finding and archived full diff, with reviewer category/severity/provenance tags removed.

Source: `diffs/10.json`; group membership: `grouping_calls/10/chunk_001_b8bbde70165e10bf.json`. Original findings and the exact classifier inputs will be retained with the classifier pilot. These observations do not override scoring judgments.

## Source review before classifier results

| Group | What the archived diff supports | Interpretation and uncertainty |
|---|---|---|
| Swapped fabricator files (17 findings) | `category_fabricator.rb` now defines `:embeddable_host`, while the new `embeddable_host_fabricator.rb` contains the former category definitions. | The mismatch is factual. Its importance is a judgment call: file organization and navigation are affected, but these findings themselves acknowledge that the definitions still load. Hypothetical future duplicate definitions are not demonstrated current bugs. This is a useful boundary case for distinguishing substantive advice from naming/organization nits; it is not an established positive advisory control. |
| Inert embedding PUT / `saveChanges` (7 findings) | `Admin::EmbeddingController#update` only renders the existing object, and `saveChanges` sends `embedding.update({})`. | A misleading or unfinished API surface is a plausible substantive advisory. A current user's failed save would require an actual caller and payload; a hypothetical future caller does not establish a present production defect. |
| Per-request host lookup / index (5 findings) | `record_for_host` performs `where("lower(host) = ?", host).first`; the new migration creates no host index. | The query and absent index are concrete. Workload, cardinality and measured latency are not established by the diff. A performance advisory can state those conditions; an unconditional claim of material slowdown is not demonstrated. |
| Duplicate host entries (4 findings) | The new model and migration contain no host uniqueness rule; the lookup selects `.first`. | The core duplicate-host/ambiguous-configuration concern is concrete. The stronger claim that `.first` has unspecified or nondeterministic ordering is not proved by this diff and depends on framework behavior. Shared root cause does not make every secondary claim in every member true. |
| Stored host with a port (4 findings) | The host validation accepts an optional port, while lookup extracts `URI(host).host` and compares that host-only value against the stored string. | A configured `example.com:8080` fails this comparison against `example.com`. This is a concrete correctness mechanism, not an advisory-only concern. Frozen verified-defect assignments remain authoritative for scoring. |

## Why this check matters

A successful JSON response establishes transport/schema validity, not classifier accuracy. A valid semantic grouping establishes complete membership, not that every merge or every secondary factual claim is correct. The report must describe accepted advisories as model-adjudicated, distinguish the new common instrument from historical judgments, and retain uncertainty rather than presenting this pilot as proof of staff-level review quality.

An earlier routing-only pilot classified duplicated authentication filters as important using knowledge about the superclass that was not shown in the diff. That is a concrete warning about the diff-only evidence boundary, not a measured classifier error rate.

## Additional negative controls, selected before their outputs

The five largest groups mostly contain concrete concerns, so they do not test rejection of low-value or false findings. Two existing PR 10 records were added:

- `ec57c390ed39`, record 47: asks to merge two imports from `ember-addons/ember-computed-decorators` into one line. The imports are visible in the diff; merging the declarations has no stated behavioral benefit. This is a pure style nit and should receive the existing penalty category.
- `f9de77efd154`, record 33: claims the admin's primary save action currently fails users without feedback. The new template has no `saveChanges` binding; host persistence uses separate actions. The present-user-impact premise is unsupported/contradicted by the shown UI, even though the unused function and no-op endpoint can support a differently worded advisory about future integration. This tests whether the classifier distinguishes the actual claim from a nearby legitimate concern.

Neither control is synthetic. Their raw findings, neutralized inputs and outputs are archived separately from final scoring.

## Observed classifier results

| Finding | GLM result | Confidence | Audit assessment |
|---|---|---|---|
| Swapped fabricator files | important_non_bug | 0.95 | Factual mismatch recognized; the staff-value versus organization-nit boundary remains subjective. |
| Inert PUT / unused save action | important_non_bug | 0.80 | Distinguishes an unfinished API surface from a demonstrated current failure. |
| Host lookup / index | important_non_bug | 0.60 | Correctly states that material latency is conditional on workload and table size. |
| Duplicate hosts | bug | 0.70 | Recognizes the core configuration problem; this does not validate every ordering claim in the group. |
| Host/port mismatch | bug | 0.90 | Recognizes the concrete mismatch described above. |
| Merge two imports | hallucination | 0.90 | Correctly applies the existing penalty category to a factual but purely stylistic comment. |
| Claimed active primary save failure | bug | 0.55 | Fails the intended negative control: the rationale acknowledges that no template wires the action and that the endpoint persists nothing, but still accepts a latent unhandled-rejection mechanism as a bug. This does not substantiate the finding's claimed current-user impact. |

Exact source identifiers and full results are in `classification_pilot/`. The last control is run `f9de77efd154`, record 33, response `35f9a12262128ce6c0e88d28ef9b6c69f021c4f698ef3322e9359e5d38e28fac.json`.

The frozen verified-bug assignments prevent this new classifier verdict from adding bug credit. However, a classifier-accepted bug outside that verified set also does not receive an unsupported-finding penalty in the current score. Consequently, this pilot reveals possible under-penalization, not merely an uncertainty in an explanatory sentence. No prompt, confidence threshold or individual scoring override was tuned to make this selected control pass. The common pass must be reported as model adjudication with observed limitations, not proof that all false claims are penalized or all accepted advisories meet an independently validated staff-level bar.
