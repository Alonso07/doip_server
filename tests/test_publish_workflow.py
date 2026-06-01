from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


def _workflow_on(workflow: dict) -> dict:
    # PyYAML follows YAML 1.1 and parses the GitHub Actions key "on" as True.
    return workflow.get("on") or workflow[True]


def test_publish_waits_for_successful_main_ci_before_publishing():
    workflow = yaml.safe_load(
        (REPO_ROOT / ".github" / "workflows" / "publish.yml").read_text()
    )

    triggers = _workflow_on(workflow)
    assert "push" not in triggers
    assert triggers["workflow_run"] == {
        "workflows": ["CI"],
        "types": ["completed"],
        "branches": ["main"],
    }

    publish_job = workflow["jobs"]["publish"]
    job_condition = " ".join(publish_job["if"].split())
    assert "github.event.workflow_run.conclusion == 'success'" in job_condition
    assert "github.event.workflow_run.event == 'push'" in job_condition
    assert "github.event.workflow_run.head_branch == 'main'" in job_condition

    checkout_step = next(
        step for step in publish_job["steps"] if step["name"].startswith("Checkout")
    )
    assert checkout_step["with"]["ref"] == "${{ github.event.workflow_run.head_sha }}"
