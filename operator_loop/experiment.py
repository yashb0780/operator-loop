"""Run the agent on every case as a LangSmith experiment and measure executable coverage.

A case is "covered" when the agent did NOT escalate AND its decision matches
the expected decision. Coverage = covered cases / total cases.
"""

import json
from datetime import datetime, timezone

from langsmith import Client

from operator_loop.agent import run_agent
from operator_loop.config import (
    DATA_FILE,
    DATASET_NAME,
    HISTORY_FILE,
    LATEST_RESULTS_FILE,
    RESULTS_DIR,
)
from operator_loop.playbook_store import current_version, read_playbook


def load_cases() -> list[dict]:
    """Read the synthetic handoff cases from data/handoffs.json."""
    return json.loads(DATA_FILE.read_text())["cases"]


def sync_dataset(client: Client) -> None:
    """Create the LangSmith dataset from the JSON file, the first time only."""
    cases = load_cases()
    if client.has_dataset(dataset_name=DATASET_NAME):
        existing = list(client.list_examples(dataset_name=DATASET_NAME))
        if len(existing) != len(cases):
            raise SystemExit(
                f"LangSmith dataset '{DATASET_NAME}' has {len(existing)} examples but the "
                f"JSON file has {len(cases)}. Delete the dataset in LangSmith and run again."
            )
        return

    print(f"Creating LangSmith dataset '{DATASET_NAME}' with {len(cases)} cases...")
    dataset = client.create_dataset(
        DATASET_NAME,
        description="SYNTHETIC sales-to-CS handoff cases for operator-loop. All companies and people are invented.",
    )
    examples = []
    for case in cases:
        # The agent sees everything except the answer key.
        visible = {k: v for k, v in case.items() if k != "expected_decision"}
        examples.append(
            {
                "inputs": {"case": visible},
                "outputs": {"expected_decision": case["expected_decision"]},
                "metadata": {"case_id": case["case_id"]},
            }
        )
    client.create_examples(dataset_id=dataset.id, examples=examples)


# ---- Scoring -------------------------------------------------------------
# LangSmith calls these once per case. Each returns a score of 0 or 1.


def is_covered(outputs: dict, reference_outputs: dict) -> bool:
    """1 if the agent handled it alone and got it right."""
    return (not outputs["escalate"]) and outputs["decision"] == reference_outputs["expected_decision"]


def covered(outputs: dict, reference_outputs: dict) -> dict:
    return {"key": "covered", "score": int(is_covered(outputs, reference_outputs))}


def escalated(outputs: dict) -> dict:
    return {"key": "escalated", "score": int(outputs["escalate"])}


def wrong_decision(outputs: dict, reference_outputs: dict) -> dict:
    """1 if the agent made a decision on its own and it was the wrong one."""
    wrong = (not outputs["escalate"]) and outputs["decision"] != reference_outputs["expected_decision"]
    return {"key": "wrong_decision", "score": int(wrong)}


def executable_coverage(outputs: list[dict], reference_outputs: list[dict]) -> dict:
    """The headline number for the whole experiment."""
    hits = sum(is_covered(o, r) for o, r in zip(outputs, reference_outputs))
    return {"key": "executable_coverage", "score": hits / len(outputs)}


# ---- Running -------------------------------------------------------------


def run_experiment() -> dict:
    """Run the full experiment with the current playbook and save the results."""
    client = Client()
    sync_dataset(client)

    playbook_text = read_playbook()
    version = current_version(playbook_text)

    def target(inputs: dict) -> dict:
        # LangSmith calls this once per case.
        return run_agent(playbook_text, inputs["case"])

    print(f"Running the agent on every case with playbook {version}...")
    results = client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[covered, escalated, wrong_decision],
        summary_evaluators=[executable_coverage],
        experiment_prefix=f"playbook-{version}",
        description=f"Executable coverage with playbook {version}",
        metadata={"playbook_version": version},
        max_concurrency=4,
    )

    # Collect one row per case, with a link to its trace.
    rows = []
    for row in results:
        run, example = row["run"], row["example"]
        out = run.outputs or {}
        expected = example.outputs["expected_decision"]
        agent_ok = "decision" in out
        rows.append(
            {
                "case_id": example.inputs["case"]["case_id"],
                "expected_decision": expected,
                "decision": out.get("decision", "error"),
                "escalate": out.get("escalate", True),
                "reason": out.get("reason", run.error or ""),
                "covered": agent_ok and is_covered(out, example.outputs),
                "run_id": str(run.id),
                "example_id": str(example.id),
                "trace_url": client.get_run_url(run=run, project_name=results.experiment_name),
            }
        )
    rows.sort(key=lambda r: r["case_id"])

    total = len(rows)
    hits = sum(r["covered"] for r in rows)
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "playbook_version": version,
        "experiment_name": results.experiment_name,
        "experiment_url": results.url,
        "covered": hits,
        "escalated": sum(r["escalate"] for r in rows),
        "wrong": sum((not r["escalate"]) and r["decision"] != r["expected_decision"] for r in rows),
        "total": total,
        "coverage": round(hits / total, 4),
    }

    # Save locally: full detail for the latest run, plus one line of history.
    RESULTS_DIR.mkdir(exist_ok=True)
    LATEST_RESULTS_FILE.write_text(json.dumps({"summary": summary, "cases": rows}, indent=2) + "\n")
    with HISTORY_FILE.open("a") as f:
        f.write(json.dumps(summary) + "\n")

    print_results(summary, rows)
    return summary


def print_results(summary: dict, rows: list[dict]) -> None:
    """Show a simple table in the terminal."""
    print()
    print(f"{'case':8} {'expected':28} {'agent':28} result")
    for r in rows:
        if r["covered"]:
            label = "covered"
        elif r["escalate"]:
            label = "escalated"
        else:
            label = "WRONG"
        print(f"{r['case_id']:8} {r['expected_decision']:28} {r['decision']:28} {label}")
    print()
    print(
        f"Playbook {summary['playbook_version']}: executable coverage "
        f"{summary['covered']}/{summary['total']} = {summary['coverage']:.0%} "
        f"({summary['escalated']} escalated, {summary['wrong']} wrong)"
    )
    print(f"Experiment: {summary['experiment_url']}")
