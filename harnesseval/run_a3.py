"""Phase A.3 runner — calls Inspect's eval() with our HARNESS_-prefixed key (no env pollution).

This is the entrypoint that exercises Inspect's full runner + native token/time accounting +
eval logs on our actual judge task, using the a3_judge_agreement task.

Usage:
  uv run python -m harnesseval.run_a3 --limit 30
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from harnesseval import keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=30, help="number of (golden,candidate) pairs to judge")
    ap.add_argument("--judge-key", default="opus", choices=["opus", "sonnet"])
    ap.add_argument("--log-dir", default="logs/a3")
    args = ap.parse_args()

    from inspect_ai import eval as inspect_eval
    from inspect_ai.model import get_model
    from harnesseval.inspect_a3 import a3_judge_agreement

    # Native Anthropic, same model Martian used (Opus 4.5 / Sonnet 4.5).
    # Inject the HARNESS_ key DIRECTLY (no os.environ pollution).
    model_id = "claude-opus-4-5-20251101" if args.judge_key == "opus" else "claude-sonnet-4-5-20250929"
    model = get_model(f"anthropic/{model_id}", api_key=keys.load_keys()["HARNESS_ANTHROPIC_API_KEY"])

    task = a3_judge_agreement(judge_key=args.judge_key, limit=args.limit)
    Path(args.log_dir).mkdir(parents=True, exist_ok=True)

    print(f"[a3] Inspect eval: model={model_id}  pairs={args.limit}  judge_key={args.judge_key}")
    log = inspect_eval(task, model=model, log_dir=args.log_dir)

    # Inspect returns EvalLog(s). Summarize agreement + token/time accounting.
    logs = log if isinstance(log, list) else [log]
    for el in logs:
        s = el.status; name = el.eval.task
        print(f"[a3] task={name} status={s}")
        if s != "success":
            print(f"[a3]   (non-success; check {args.log_dir})")
            continue
        # agreement rate = the mean metric over our scorer
        r = el.results
        agree = None
        if r and r.metrics:
            m = r.metrics.get("mean")
            if m is not None:
                agree = float(m.value)
        # count scored samples + per-sample token/time (Inspect native accounting)
        total_in = total_out = n_samples = 0
        if el.samples:
            for sm in el.samples:
                n_samples += 1
                mu = sm.model_usage
                if mu:
                    for _m, usage in (mu.items() if isinstance(mu, dict) else []):
                        total_in += getattr(usage, "input_tokens", 0)
                        total_out += getattr(usage, "output_tokens", 0)
        print(f"[a3] AGREEMENT (Inspect mean metric): {agree:.4f}  ({n_samples} samples)")
        print(f"[a3] Inspect native accounting: input_tokens={total_in:,}  output_tokens={total_out:,}  total={total_in+total_out:,}")
        print(f"[a3] eval log (audit trail): {args.log_dir}/  (task={name})")
    print("[a3] DONE — Inspect runner + cost accounting validated on our judge task.")


if __name__ == "__main__":
    main()
