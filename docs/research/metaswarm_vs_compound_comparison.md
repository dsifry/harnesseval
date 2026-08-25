# metaswarm vs Compound Engineering — agent/rubric comparison (2026-08-24)

Three parallel subagent comparisons of metaswarm's ~20 agents + ~9 rubrics vs Compound
Engineering's ce-code-review personas, to identify what metareview (simplified from metaswarm
into 6 lenses) lost, and what it should borrow. Context: metareview reduced metaswarm's
security-auditor + security-design + architect + code-review + adversarial + test + release
agents/rubrics into 6 artifact-shape lenses (Feasibility, Completeness, Scope, Architecture,
Intent, Security). This asks: was that simplification lossy, and what's worth re-borrowing?

## A. Security (metaswarm security-auditor + security-design + security-review-rubric vs Compound security-reviewer)

### Coverage metaswarm has that metareview's single lens loses
- IDOR/ownership scoping + multi-tenant organizationId enforcement (A01 sub-item)
- Injection variants beyond SQL: command (exec/spawn), NoSQL (JSON.parse as query), LDAP/XPath, deserialization
- SSRF protocol-bypass (file://, gopher://, naive localhost string check)
- Session fixation/rotation, secrets-in-LOGS (distinct from secrets-in-code)
- A full STRIDE threat-modeling phase (security-DESIGN agent) — pre-implementation, design-stage
- Project-vertical checks (Stripe webhook sig, Gmail OAuth, PII-in-analytics) — repo-specific

### Compound's distinctive addition
- Anchored confidence rubric (0/25/50/75/100) + P0-P3 severity gate, with a LOWERED reporting
  threshold for security ("anchor 50 + P0 survives the gate")
- Explicit "what you don't flag" suppression list (no defense-in-depth on already-protected code,
  no dev-config HTTP, no generic hardening without a specific exploit)
- "Trace data from entry to dangerous sink" attacker framing (vs checklist matching)

### What metareview should borrow
- From metaswarm: IDOR/ownership scoping; injection variants (command/NoSQL/deserialization);
  SSRF protocol-bypass; secrets-in-logs. (One-line each, concrete diff-detectable sinks.)
- From Compound: the anchored confidence rubric + lowered threshold; the suppression list; the
  attacker-trace framing (more token-efficient than checklist matching).
- Skip (non-diff-reviewable): STRIDE threat-modeling, weighted scoring, project verticals,
  pnpm audit/CVE scanning, session timeout/MFA posture, alerting/monitoring, webhook sig/OAuth
  rotation where configured outside the diff.

## B. Architecture/Correctness (metaswarm architect + code-review + architecture-rubric + code-review-rubric vs Compound correctness/performance/maintainability/reliability/api-contract)

### Coverage metaswarm has that metareview's single Architecture lens loses
- Plan-time architecture gating (service-layer placement, DI, pattern selection, DB schema
  planning) — metaswarm evaluates plans BEFORE code; a post-impl lens can't gate at plan time.
- Adversarial DoD-contract mode (binary PASS/FAIL vs Definition-of-Done) — metareview's lens
  reviews code quality, not "does it meet the spec."
- Project-specific hygiene (TS `as any` ban, `as never` for test DI, shared Prisma factory) —
  concrete codebase gates a generic lens won't carry.

### What Compound's 5 personas cover that metareview's single lens covers worse/not-at-all
- Correctness: sentinel-meaning-change auditing (a returned null/empty now meaning a new state),
  React effect lifecycle asymmetry (cleanup/effect-path enumeration), tooling/provisioning invariant fidelity
- Performance: 5 distinct failure classes (N+1, unbounded memory, missing pagination, hot-path
  allocations, blocking-I/O-in-async) with a HIGHER suppression threshold (avoid premature-opt noise)
- Maintainability: "complexity moved, not removed" detection, 1000-line file-size regression,
  thin-wrapper/identity-abstraction flagging, sibling-path/comment drift, premature-abstraction
- Reliability: retry-without-backoff/jitter, missing timeouts, catch-and-ignore swallowing,
  cascading-failure path tracing, STAND-IN GUARD FIDELITY (CI gate that doesn't mirror production)
- API contract: breaking-change detection (renamed/removed fields, narrowed inputs, widened
  returns), missing versioning on breaking changes, sentinel contract overloads

### Granularity tradeoff: 1 lens vs 5 personas
- The split IS worth it for findings quality. Each Compound persona has a distinct "what you
  don't flag" list that prevents overlap (correctness defers slow code to performance; performance
  defers logic bugs to correctness; etc.) — this NEGATIVE scoping is the anti-overlap mechanism
  metaswarm's single rubric lacks, so a single reviewer either skips persona-specific classes or
  duplicates effort.
- Each persona has a domain-tuned confidence anchor (performance has a higher threshold to
  suppress speculative findings; correctness has anchor-100=mechanical trace).
- BUT the fanout cost is real (5 subagents vs 1) — on opus where lenses are free (haiku) this is
  cheap; on codex where the orchestrator is 100% of cost, 5 personas is 5× the fanout.

### What metareview should borrow
- Compound's correctness persona: sentinel-meaning-change auditing + effect-lifecycle asymmetry
  (metareview's Architecture lens covers "semantic correctness" but doesn't enumerate these)
- Compound's maintainability persona: "complexity moved not removed" + file-size regression +
  thin-wrapper flagging (structural regression detection the single lens lacks)
- Compound's reliability persona: cascading-failure tracing + stand-in guard fidelity (CI gate
  fidelity) — distinct production-failure discipline
- Compound's api-contract persona: breaking-change + versioning discipline (metaswarm's "API
  Design" covers REST conventions but no breaking-change/migration discipline)
- The NEGATIVE-SCOPING pattern: each lens should have a "what you don't flag" list to prevent
  overlap (borrow from Compound's personas).

## C. Adversarial/Testing/Edge (metaswarm adversarial + test-coverage + release-engineering rubrics + test-automator/release-engineer agents vs Compound adversarial/testing/data-migration/deployment personas)

### metareview has NO LLM adversarial lens, NO testing-quality lens, NO release/deploy lens
metaswarm's deterministic gates flag missing-test/TODO/eval/duplicate-path but do not reason about
WHAT tests verify or whether behavior is adversarially unsafe.

### The adversarial lens question: YES, metareview should fill this gap
metareview's 5 artifact-shape lenses are all COLLABORATIVE ("does the artifact match intent / is
it well-shaped"). None assume the change is hostile/buggy. An adversarial lens catches:
- Assumption violations ("code assumes the queue is never empty - what if it is?") — Intent
  checks intent-match, not negation of intent
- Composition/cascade failures that Scope (single-diff) and Architecture (shape) can't trace —
  these live BETWEEN components
- SILENT-PASS VERIFICATION FAILURES — a gate that goes green while production is red. Security
  checks for vulns, not for fidelity of the guard itself. Highest-value, lowest-overlap addition.
metaswarm's adversarial rubric is contract-verification (PASS/FAIL vs DoD); Compound's is
constructive-attack (build the breaking input). metareview should adopt Compound's
constructive-attack style — diff-reviewable, composes with existing lenses, no DoD needed.

### The testing lens question: YES, metareview should add a testing-quality LLM lens
The deterministic missing-test gate only flags ABSENCE of a test file. It cannot detect:
- Tests that exist but assert toBeTruthy()/"doesn't throw" (false confidence)
- Behavioral change in the diff with ZERO test modifications (the strongest diff signal)
- Tests verifying mocks rather than real logic
metaswarm's rubric is prescriptive (100% coverage mandate, factory patterns, project-coupled);
Compound's is diagnostic + diff-anchored, which fits metareview's generic-eval role better.

### What metareview should borrow (diff-reviewable only)
- From metaswarm adversarial: BLOCKING/WARNING severity + mandatory file:line evidence rule
  (no assertion without citation); file-scope gate (changed files must be within diff)
- From Compound adversarial: constructive-attack framing (assumption-violation, composition-
  failure, cascade, abuse-cases, silent-pass-verification-mechanism fidelity)
- From Compound testing: untested new branches, false-confidence assertions, behavioral-change-
  without-test-work trigger, mirror-tests-that-miss-the-machine
- From Compound data-migration: schema-drift (git-diff against review-base), irreversible
  migrations, missing backfills, deploy-window breaks, dual-write gaps, silent data loss
- Skip (non-diff): release-engineering 7-gate pipeline (pre-merge/CI/soak/post-deploy/rollback) —
  runtime/operational; metaswarm's release rubric is almost entirely NOT diff-reviewable.
  Compound's deployment-verification-agent is diff-anchored (produces a checklist from the PR) —
  borrowable but lower priority.

## Synthesis: what metareview lost in the simplification + what to re-borrow

### Confirmed losses (the 6-lens simplification dropped real coverage)
1. NO adversarial lens (all 6 lenses are collaborative; none assume hostility). Compound + metaswarm
   both have dedicated adversarial reviewers. This is the biggest gap.
2. NO testing-quality LLM lens (only a deterministic missing-test gate). Can't detect false-
   confidence tests or behavioral-change-without-test-work.
3. Security lens is OWASP-checklist-level; loses metaswarm's IDOR/ownership scoping, injection
   variants (command/NoSQL/deserialization), SSRF protocol-bypass, secrets-in-logs.
4. Architecture lens covers semantic correctness but lacks Compound's sentinel-meaning-change,
   effect-lifecycle, "complexity moved not removed", cascading-failure, stand-in-guard-fidelity,
   api-contract breaking-change/versioning checks.
5. NO data-migration lens (schema-drift, irreversible migrations, missing backfills).

### Highest-value re-borrows (diff-reviewable, cheap, low-overlap)
- Adversarial lens (constructive-attack + silent-pass-verification-fidelity) — NEW 7th lens
- Testing-quality lens (false-confidence + behavioral-change-without-test-work) — NEW 8th lens
- Security: graft IDOR/ownership + injection variants + SSRF protocol-bypass + secrets-in-logs
  (one-line each into the existing Security lens)
- Architecture: graft sentinel-meaning-change + cascading-failure + stand-in-guard-fidelity +
  api-contract-breaking-change (into the existing Architecture lens)
- ALL lenses: add a "what you don't flag" suppression list (Compound's anti-overlap mechanism) +
  the anchored confidence rubric (P0-P3 + 0/25/50/75/100)

### Not worth re-borrowing (non-diff or not worth the complexity)
- metaswarm's plan-time architect gating (pre-code), STRIDE threat-modeling, weighted scoring
  rubrics, project-vertical checks (Stripe/Gmail), pnpm audit/CVE, release 7-gate pipeline,
  session/MFA/monitoring posture — all runtime/design-time, not diff-reviewable.
