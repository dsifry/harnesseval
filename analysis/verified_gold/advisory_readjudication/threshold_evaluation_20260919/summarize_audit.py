"""Join the pre-unblinding audit to saved classifier metadata and render findings.
Run after select_sample.py and audit_before_unblinding.py. No classifier/API calls.
"""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
P = Path(__file__).resolve().parent
ROOT = P.parents[3]
pop = json.loads((P/'population.json').read_text())
key = json.loads((P/'sample_key.json').read_text())
audit = json.loads((P/'audit_before_unblinding.json').read_text())
by_id = {r['audit_id']:r for r in audit['judgments']}
rows = [{**r, **by_id[r['audit_id']]} for r in key['samples']]
assert len(rows)==47 and len(by_id)==47
for r in pop['rows']:
    assert hashlib.sha256((ROOT/r['source']).read_bytes()).hexdigest()==r['sha256'], r['source']
counts=defaultdict(Counter)
for r in rows: counts[(r['category'],r['band'])][r['audit_outcome']]+=1
labels={'S':'Supported useful advisory', 'N':'Needs context or narrowing', 'L':'Unsupported or low value', 'B':'Bug/missing-feature candidate; not automatic advisory credit'}
lines=['# Advisory confidence discriminator evaluation — 19 September 2026', '',
'**Recommendation: use advisory confidence ≥0.70 as a provisional primary policy, retain ≥0.80 for unsupported/style penalties, and show ≥0.60 and ≥0.80 advisory sensitivity results. Do not adopt ≥0.50.** If one common discriminator is mandatory, retain ≥0.80 until a larger independent audit supports changing both credit and penalties together. No production policy or frozen runner was changed by this evaluation.', '',
'This recommendation reflects a tradeoff: recover concrete regression-prevention and schema-hardening advice excluded at 0.80 while avoiding the much weaker marginal evidence below 0.70. It is not an empirically calibrated optimum. The cost of mistakenly crediting advice versus mistakenly penalizing a reviewer has not been measured; keeping the penalty gate at 0.80 is a conservative policy judgment, not a finding that 0.80 is calibrated.', '',
'## Population and scoring limits', '',
'All 10,057 independent classifier claims across six PRs have saved judgments. The 101 reused audited bug identities are excluded from this population. The table counts raw classifier votes before semantic deduplication, verified-bug overlap exclusion, or aggregation into selected reviews. These are NOT final credited advisory identities, observed developer benefits, or F2′ scores. T and D remain frozen; classifier bug labels do not create new verified bugs.', '',
'| Inclusive cutoff | Raw advisory candidates | Added versus next stricter cutoff | Raw penalty candidates if the same cutoff were used |',
'|---|---:|---:|---:|']
for threshold,delta in [('0.5',229),('0.6',595),('0.7',822),('0.8',None)]:
    c=pop['threshold_counts'][threshold]
    lines.append(f"| ≥{threshold} | {c['important_non_bug']:,} | {delta if delta is not None else 'Baseline'} | {c['hallucination']:,} |")
lines += ['', 'Lowering advisory credit to 0.70 admits 822 additional raw candidates (+121% relative to 679 at 0.80). Lowering further to 0.60 adds 595; to 0.50 adds 229, including 165 at exactly 0.55. A common 0.70 cutoff also raises raw penalty candidates from 494 to 955 (+461); that is a separate policy change, not a free side effect of recognizing more advice.', '',
'## Audit design and results', '',
'Fixed-seed, hash-ordered sampling selected three raw advisory claims per confidence band per representative framework (vanilla-engineered, compound-realistic, metareview-realistic): nine per band, 36 total. Eleven additional penalty-label claims were sampled, one per populated band/framework stratum; vanilla has no penalty claim in [0.50,0.60). Representative framework means the cached claim’s source review, not all frameworks that emitted the same claim. This samples claims, not semantic identities; related test-gap claims recur.', '',
'One assistant reviewed original claim wording against the frozen PR diffs before opening the classifier category/confidence key, and saved judgments before unblinding. Original prose was not redacted: several claims contain the original reviewer’s own confidence or severity. Thus this is metadata-hidden, not fully blinded. No classifier reasoning was used to choose the audit judgments. This is an exploratory audit, not an independent human gold standard or measured population precision.', '',
'“Supported” means the main actionable advisory is supported by available evidence without a material unsupported premise. “Needs context or narrowing” is not a hallucination finding: a claim may have a useful core but overstate coverage, causality, or consequences. “Unsupported or low value” combines demonstrably unsupported claims and true but minor cleanup/style. B flags category ambiguity where bug handling must precede advisory credit. Test-gap findings establish absence of relevant added tests in the diff, not an exhaustive absence of repository-wide coverage.', '',
'| Classifier advisory band | Supported | Needs context/narrowing | Unsupported/low value | Bug-category question |',
'|---|---:|---:|---:|---:|']
for band in ['0.5–<0.6','0.6–<0.7','0.7–<0.8','0.8–1.0']:
    c=counts[('important_non_bug',band)]
    lines.append(f"| {band} | {c['S']}/9 | {c['N']} | {c['L']} | {c['B']} |")
lines += ['', 'The small equally allocated strata cannot support population precision estimates, confidence calibration, framework rankings, or a statistically established superiority of 0.70 over 0.80. In particular, 5/9 versus 6/9 is not persuasive evidence of a measurable quality difference. It does show concrete useful findings in the 0.70 band, while both lower bands contain substantial unsupported assumptions and minor cleanup. Decisions depend on the strictness of the full-claim rubric: many N claims could become useful if narrowed, but silently rewriting them would evaluate a different review.', '',
'Penalty spot-check: 8 of 11 claims were unsupported or low value; 3 required more context. None was clearly supported useful advice under this rubric, but one claim per stratum is far too little to estimate false-penalty rates. A lack of supporting context does not establish that a claim is false. Do not relabel all N cases as hallucinations.', '',
'## Concrete evidence', '',
'- S47 (0.70): schema-level absence of a category foreign key is a concrete hardening advisory; the claim limits itself to schema-level protection. This is useful below 0.80.',
'- S25 (0.70): Office365 error handling changes from logging a failed parse to a throwing parser without a corresponding added test. This identifies a specific regression-prevention benefit.',
'- S21 (0.60): nonstandard-port and already-absolute URL invariants lack added tests. This is a useful finding below 0.70; the proposed cutoff knowingly loses some real advice.',
'- S14 (0.60): claim says an invalid-URL test would pass without its rescue. URI parsing occurs before host comparison; a local Ruby 2.6.10 check raises URI::InvalidURIError for “not a url.” The claimed mechanism is contradicted, although the historical project runtime was not reproduced.',
'- S10 (0.70): controller test gaps are real, but the same claim also says normalization/host-lookup tests are absent when the diff explicitly adds them. A score of 0.70 does not guarantee a wholly correct claim.',
'- S41 (penalty label, 0.60): alleged empty encryption-key execution is contradicted by APP_CREDENTIAL_SHARING_ENABLED requiring both keys and the early 403 gate. The workflow can identify false premises, but this one-pass classifier is not an independent second hallucination audit.', '',
'## What changes in the statistics', '',
'For α=1, F2′=(5T+A)/(4D+T+A+H). With T, D and H fixed, admitting an additional deduplicated advisory increases F2′ (except an already perfect score). Therefore merely getting a higher F2′ at a lower advisory threshold is not evidence that the lower threshold is more valid. Lowering H’s cutoff at the same time can offset or reverse that change. Which framework benefits depends on per-review advisory/penalty counts after deduplication, not the global raw totals above.', '',
'Recompute each advisory policy with the same frozen T/D and H cutoff, exact selected-review coverage, verified-bug exclusion, and policy-specific semantic deduplication. Reuse validated equivalence evidence where valid, but inspect boundaries previously separated by category/threshold; do not just append raw new claims to old A counts. Compare paired scores, rankings and recommendations at advisory cutoffs 0.60/0.70/0.80. Final PR deduplication/export was still in progress during this evaluation (5/6 PRs, 337/403 exported reviews), so no complete F2′ sensitivity or ranking claims are made here.', '',
'Processed findings below a scoring threshold remain classified findings with their original category/confidence. They are not “unresolved.” Keep incomplete jobs and scoring-policy exclusions separate.', '',
'## Reproduction and audit trail', '',
'Run `python3 select_sample.py`, `python3 audit_before_unblinding.py`, and `python3 summarize_audit.py` from this directory (or use their absolute paths). Selection and tables are deterministic; audit judgments are recorded expert-assistant assessments and are not mechanically derived truth. Re-running the judgment-recording script reproduces the saved assessments, not a new blinded audit. Source SHA-256 hashes are verified for every population record by this summarizer. Frozen diff hashes are recorded in audit_summary.json. No production sources are written.', '',
f"Seed: `{key['seed']}`. Pass digest: `{pop['pass_digest']}`.", '', '## Full 47-claim audit', '']
for r in rows:
    lines += [f"### {r['audit_id']} — {labels[r['audit_outcome']]}", '',
              f"Classifier: {r['category']}, confidence {r['confidence']}; representative framework: {r['representative_framework']}.", '',
              '> '+r['claim'].replace('\n','\n> '), '', r['audit_reason'], '',
              f"Evidence: [frozen PR diff]({P/r['evidence_diff']}); [saved verdict]({ROOT/r['source']}).", '']
(P/'EVALUATION.md').write_text('\n'.join(lines))
(P/'audit_summary.json').write_text(json.dumps({'pass_digest':pop['pass_digest'], 'threshold_counts':pop['threshold_counts'], 'audit_counts':[{'category':k[0],'band':k[1],**dict(v)} for k,v in sorted(counts.items())], 'diff_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in P.glob('*.diff')}, 'judgments_sha256':hashlib.sha256((P/'audit_before_unblinding.json').read_bytes()).hexdigest(), 'rows':rows},indent=2))
print('Verified 10,057 source hashes; wrote EVALUATION.md and audit_summary.json.')
print('Example exact confidences:',[(r['audit_id'],r['confidence']) for r in rows if r['audit_id'] in ['S47','S25','S21','S14','S10','S41']])
