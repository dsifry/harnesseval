# Matched adjudicator pilots

Each pilot repeats seven saved PR10 findings and one 30-text grouping workload at concurrency four and then six. The complete PR diff, classifier rubric, grouping prompt, findings and inclusive 0.80 gate are identical. High thinking uses the repository effort label `xhigh`, which maps to API `reasoning_effort="high"`; low maps to `low`. Temperature is 1 under the shared router. These are isolated pilot artifacts, not production judgments.

| Model | Thinking | Batch at 4 (s) | Batch at 6 (s) | Model-category agreement | Agreement after 0.80 gate | Groups, first / repeat | Errors |
|---|---|---:|---:|---:|---:|---:|---:|
| [DeepSeek Flash](pilots/deepseek_flash_low_v1/comparison.json) | low | 70.2 | 42.4 | 6/7 | 5/7 | 14 / 10 | 0 |
| [DeepSeek Flash](pilots/deepseek_flash_high_v1/comparison.json) | high | 56.0 | 53.1 | 7/7 | 5/7 | 9 / 9 | 0 |
| [GLM Flash](pilots/glm_flash_low_v1/comparison.json) | low | 13.5 | 13.2 | 6/7 | 4/7 | 9 / 9 | 0 |
| [GLM Flash](pilots/glm_flash_high_v1/comparison.json) | high | 24.7 | 35.1 | 6/7 | 4/7 | 10 / 12 | 0 |
| [GLM base](pilots/glm_base_low_v1/comparison.json) | low | 47.9 | 57.9 | 7/7 | 6/7 | 9 / 9 | 0 |

## Findings and limits

- All 32 high-thinking trial requests completed successfully. High thinking did not increase gated agreement in these probes: DeepSeek remained 5/7 and GLM Flash remained 4/7. This is repeat agreement, not a measured accuracy rate.
- GLM Flash high credited the false active-save claim as `important_non_bug` at confidence 0.80 in its six-concurrent repeat. The raw rationale describes a primary save action, but the new embedding template contains only the host controls and `addHost`, with no `saveChanges` binding. A hypothetical unused method is not evidence of the claimed active user failure. See the [raw verdict](pilots/glm_flash_high_v1/concurrency_6/35f9a12262128ce6c0e88d28ef9b6c69f021c4f698ef3322e9359e5d38e28fac.json) and [archived diff](diffs/10.json).
- Grouping indices 12, 18, 19, 20 and 23 mix nonunique category-name selection, case/rename mismatch, and incompatible crash-versus-fallback claims. DeepSeek high merged all five on both repeats. GLM Flash high separated some of them, but changed its partition between repeats and retained mixtures of materially different claims. A shared file/line is insufficient to propagate one representative verdict to these texts.
- All grouping trials merged the two deliberately repeated exact-text controls. That limited check does not validate the other merges.
- Timing is observational. The six-concurrent stage always follows the four-concurrent stage, and cache/provider warmup and load can affect results. The sample is deliberately selected from one PR; it is not a random or representative accuracy benchmark, and small agreement differences do not establish general model superiority.
- No pilot has been promoted to the production scoring pass. Existing audited bug assignments and report scores are unchanged by these trials.
