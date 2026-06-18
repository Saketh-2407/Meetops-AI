"""Evaluation harness for the agentic extraction pipeline.

Scores action-item precision/recall, owner accuracy, deadline accuracy, and
output schema validity against tests/evaluation_set.json.

Runs each transcript through the graph only up to the human_approval
interrupt (the same point /analyze stops at) and never calls /resume, so
execute_actions — and therefore Gmail/Calendar/GitHub — never runs. The
imported `meeting_graph` also defaults to InMemorySaver, so this needs no
running Postgres.

Usage (from repo root, with backend/venv active):
    python tests/run_evaluation.py
"""
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.agents.graph import meeting_graph  # noqa: E402

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVAL_SET_PATH = os.path.join(os.path.dirname(__file__), "evaluation_set.json")

REQUIRED_ACTION_ITEM_KEYS = {"id", "task", "owner", "deadline", "priority", "status", "type"}


def validate_schema(result: dict) -> tuple[bool, list[str]]:
    errors = []

    def check(key, expected_type):
        if key not in result:
            errors.append(f"missing key '{key}'")
        elif not isinstance(result[key], expected_type):
            errors.append(f"'{key}' should be {expected_type.__name__}, got {type(result[key]).__name__}")

    check("meeting_title", str)
    check("executive_summary", str)
    check("key_points", list)
    check("decisions", list)
    check("action_items", list)
    check("risks_or_blockers", list)
    check("calendar_suggestions", list)
    check("follow_up_email", dict)

    for i, item in enumerate(result.get("action_items", [])):
        if not isinstance(item, dict):
            errors.append(f"action_items[{i}] is not a dict")
            continue
        missing = REQUIRED_ACTION_ITEM_KEYS - item.keys()
        if missing:
            errors.append(f"action_items[{i}] missing keys: {sorted(missing)}")

    return (len(errors) == 0), errors


def _norm(s):
    return (s or "").strip().lower()


def _owner_matches(expected_owner, actual_owner) -> bool:
    if expected_owner is None:
        return not actual_owner
    return _norm(expected_owner) == _norm(actual_owner)


def _deadline_matches(expected_contains, actual_deadline) -> bool:
    if expected_contains is None:
        return not actual_deadline
    e, a = _norm(expected_contains), _norm(actual_deadline)
    return bool(a) and (e in a or a in e)


def _task_matches(keywords, actual_task) -> bool:
    actual = _norm(actual_task)
    return all(_norm(kw) in actual for kw in keywords)


def score_action_items(expected_items: list[dict], actual_items: list[dict]) -> dict:
    """Greedy bipartite match: each expected item claims the first unused
    actual item whose task text contains all its keywords."""
    unmatched_actual = list(actual_items)
    matches = []  # (expected, actual)
    unmatched_expected = []

    for exp in expected_items:
        match = next((a for a in unmatched_actual if _task_matches(exp["task_keywords"], a.get("task"))), None)
        if match is not None:
            matches.append((exp, match))
            unmatched_actual.remove(match)
        else:
            unmatched_expected.append(exp)

    tp = len(matches)
    fp = len(unmatched_actual)
    fn = len(unmatched_expected)

    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    owner_correct = sum(1 for exp, act in matches if _owner_matches(exp["owner"], act.get("owner")))
    deadline_correct = sum(1 for exp, act in matches if _deadline_matches(exp["deadline_contains"], act.get("deadline")))

    owner_accuracy = owner_correct / tp if tp else None
    deadline_accuracy = deadline_correct / tp if tp else None

    return {
        "tp": tp, "fp": fp, "fn": fn,
        "precision": precision, "recall": recall, "f1": f1,
        "owner_accuracy": owner_accuracy, "deadline_accuracy": deadline_accuracy,
        "matches": matches,
        "missed_expected": unmatched_expected,
        "extra_actual": unmatched_actual,
    }


def run_transcript(entry: dict) -> dict:
    transcript_path = os.path.join(REPO_ROOT, entry["transcript_file"])
    transcript = open(transcript_path, encoding="utf-8").read()

    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    # Runs summary -> decision -> action -> email -> calendar -> human_approval,
    # then interrupt() pauses the graph and returns. execute_actions (and
    # therefore every real tool call) only runs if we invoke with
    # Command(resume=...), which this harness never does.
    result = meeting_graph.invoke({"transcript": transcript}, config=config)

    schema_valid, schema_errors = validate_schema(result)
    item_scores = score_action_items(entry["expected_action_items"], result.get("action_items", []))

    return {
        "meeting_id": entry["meeting_id"],
        "schema_valid": schema_valid,
        "schema_errors": schema_errors,
        "item_scores": item_scores,
        "raw_action_items": result.get("action_items", []),
    }


def fmt_pct(x):
    return "-" if x is None else f"{x * 100:.0f}%"


def print_summary_table(results: list[dict]):
    rows = []
    for r in results:
        s = r["item_scores"]
        rows.append((
            r["meeting_id"],
            f"{s['precision'] * 100:.0f}%",
            f"{s['recall'] * 100:.0f}%",
            f"{s['f1'] * 100:.0f}%",
            fmt_pct(s["owner_accuracy"]),
            fmt_pct(s["deadline_accuracy"]),
            "Yes" if r["schema_valid"] else "No",
        ))

    total_tp = sum(r["item_scores"]["tp"] for r in results)
    total_fp = sum(r["item_scores"]["fp"] for r in results)
    total_fn = sum(r["item_scores"]["fn"] for r in results)
    micro_precision = total_tp / (total_tp + total_fp) if (total_tp + total_fp) else 1.0
    micro_recall = total_tp / (total_tp + total_fn) if (total_tp + total_fn) else 1.0
    micro_f1 = (2 * micro_precision * micro_recall / (micro_precision + micro_recall)) if (micro_precision + micro_recall) else 0.0

    all_owner = [r["item_scores"]["owner_accuracy"] for r in results if r["item_scores"]["owner_accuracy"] is not None]
    all_deadline = [r["item_scores"]["deadline_accuracy"] for r in results if r["item_scores"]["deadline_accuracy"] is not None]
    overall_owner = sum(all_owner) / len(all_owner) if all_owner else None
    overall_deadline = sum(all_deadline) / len(all_deadline) if all_deadline else None
    all_schema_valid = all(r["schema_valid"] for r in results)

    header = ("Transcript", "Precision", "Recall", "F1", "Owner Acc.", "Deadline Acc.", "Schema Valid")
    rows.append((
        "**Overall**",
        f"{micro_precision * 100:.0f}%", f"{micro_recall * 100:.0f}%", f"{micro_f1 * 100:.0f}%",
        fmt_pct(overall_owner), fmt_pct(overall_deadline),
        "Yes" if all_schema_valid else "No",
    ))

    widths = [max(len(str(h)), *(len(str(row[i])) for row in rows)) for i, h in enumerate(header)]

    def fmt_row(row):
        return "| " + " | ".join(str(c).ljust(w) for c, w in zip(row, widths)) + " |"

    print(fmt_row(header))
    print("|" + "|".join("-" * (w + 2) for w in widths) + "|")
    for row in rows:
        print(fmt_row(row))


def print_breakdown(results: list[dict]):
    for r in results:
        s = r["item_scores"]
        print(f"\n=== {r['meeting_id']} ===")
        if not r["schema_valid"]:
            print(f"  SCHEMA ERRORS: {r['schema_errors']}")

        for exp, act in s["matches"]:
            owner_ok = "OK" if _owner_matches(exp["owner"], act.get("owner")) else "MISMATCH"
            deadline_ok = "OK" if _deadline_matches(exp["deadline_contains"], act.get("deadline")) else "MISMATCH"
            print(f"  MATCHED  expected={exp['task_keywords']} -> actual='{act.get('task')}'")
            print(f"           owner: expected={exp['owner']!r} actual={act.get('owner')!r} [{owner_ok}]")
            print(f"           deadline: expected_contains={exp['deadline_contains']!r} actual={act.get('deadline')!r} [{deadline_ok}]")

        for exp in s["missed_expected"]:
            print(f"  MISSED (false negative): expected keywords={exp['task_keywords']}, owner={exp['owner']}")

        for act in s["extra_actual"]:
            print(f"  EXTRA (false positive): actual='{act.get('task')}' owner={act.get('owner')}")


def main():
    with open(EVAL_SET_PATH, encoding="utf-8") as f:
        eval_set = json.load(f)

    results = [run_transcript(entry) for entry in eval_set]

    print("\n# Evaluation Results\n")
    print_summary_table(results)
    print("\n## Per-transcript breakdown")
    print_breakdown(results)


if __name__ == "__main__":
    main()
