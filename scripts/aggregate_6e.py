"""Bonus 6e - aggregate repeated evaluation runs: mean and range per condition and per task.

    python scripts/aggregate_6e.py                      # reads results-6e/*/ (repeats) and results/ (main run)
    python scripts/aggregate_6e.py --repeats results-6e --main results

Each repeat is a folder <repeats>/<name>/<condition>/<task>/run.json (same layout as results/).
Only evaluation tasks are used. Prints Markdown.
"""
import argparse
import json
import statistics as st
from pathlib import Path

CONDITIONS = ["baseline", "subagents", "skills-auto"]


def load(results_dir: Path) -> dict[tuple[str, str], dict]:
    """{(condition, task): record} for the evaluation tasks of one results folder."""
    out = {}
    for p in sorted(results_dir.glob("*/*/run.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        if p.parent.parent.name in CONDITIONS and r.get("role") == "eval":
            out[(p.parent.parent.name, r["task"])] = r
    return out


def mean_score(runs: dict, condition: str) -> float | None:
    rs = [r["score"] for (c, _), r in runs.items() if c == condition]
    return sum(rs) / len(rs) if rs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", default="results-6e")
    ap.add_argument("--main", default="results")
    args = ap.parse_args()

    reps = {p.name: load(p) for p in sorted(Path(args.repeats).iterdir()) if p.is_dir()}
    main_runs = load(Path(args.main))
    tasks = sorted({t for r in reps.values() for (_, t) in r})
    print(f"Repeats: {', '.join(reps)} ({len(reps)} per cell). Scores = share of checks passed.\n")

    print("### Mean score over the evaluation tasks, per repeat\n")
    print("| condition | " + " | ".join(reps) + " | mean | min-max | sd | main run (other model) |")
    print("|---|" + "---|" * (len(reps) + 4))
    for c in CONDITIONS:
        vals = [mean_score(r, c) for r in reps.values()]
        vals = [v for v in vals if v is not None]
        if not vals:
            continue
        m = mean_score(main_runs, c)
        main_cell = f"{m:.2f}" if m is not None else "-"
        print(f"| {c} | " + " | ".join(f"{v:.2f}" for v in vals)
              + f" | {sum(vals) / len(vals):.2f} | {min(vals):.2f}-{max(vals):.2f}"
              + f" | {st.pstdev(vals):.2f} | {main_cell} |")

    print("\n### Per task: passed/total in each repeat, and mean score\n")
    print("| task | condition | " + " | ".join(reps) + " | mean | main run |")
    print("|---|---|" + "---|" * (len(reps) + 2))
    for t in tasks:
        for c in CONDITIONS:
            cells, scores = [], []
            for r in reps.values():
                rec = r.get((c, t))
                cells.append(f"{rec['passed']}/{rec['total']}" if rec else "-")
                if rec:
                    scores.append(rec["score"])
            mr = main_runs.get((c, t))
            mean_cell = f"{sum(scores) / len(scores):.2f}" if scores else "-"
            main_cell = f"{mr['passed']}/{mr['total']}" if mr else "-"
            print(f"| {t} | {c} | " + " | ".join(cells) + f" | {mean_cell} | {main_cell} |")

    print("\n### Cost and behaviour (mean per run)\n")
    print("| condition | tokens (repeats) | tokens (main) | tool calls | subagent calls | runs reading a skill | runs with error |")
    print("|---|---|---|---|---|---|---|")
    for c in CONDITIONS:
        rs = [r for rep in reps.values() for (cc, _), r in rep.items() if cc == c]
        ms = [r for (cc, _), r in main_runs.items() if cc == c]
        if not rs:
            continue
        n = len(rs)
        print(f"| {c} | {sum(r['tokens']['total'] for r in rs) // n:,} "
              f"| {sum(r['tokens']['total'] for r in ms) // max(len(ms), 1):,} "
              f"| {sum(r['tool_calls'] for r in rs) / n:.1f} | {sum(r['subagent_calls'] for r in rs) / n:.1f} "
              f"| {sum(1 for r in rs if r['skills_read'] > 0)}/{n} | {sum(1 for r in rs if r.get('error'))}/{n} |")


if __name__ == "__main__":
    main()
