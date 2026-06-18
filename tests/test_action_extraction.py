"""Minimal smoke test for the action agent.

Run from backend/:  pytest ../tests/test_action_extraction.py
Requires OPENAI_API_KEY in the environment. This is a starting point;
extend it into the precision/recall evaluation described in the README.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.agents.action_agent import action_agent  # noqa: E402

SAMPLE = (
    "Sarah: John, please complete load testing by Thursday evening.\n"
    "Priya: I can fix the onboarding bugs by Wednesday.\n"
)


def test_action_agent_extracts_items():
    result = action_agent({"transcript": SAMPLE})
    items = result["action_items"]
    assert isinstance(items, list)
    assert len(items) >= 1
    assert all("task" in i and "status" in i for i in items)
    assert all(i["status"] == "pending_approval" for i in items)
