"""Prevent the split CodeQL action updates that broke Dependabot's scans."""

import re
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def assert_codeql_actions_aligned(workflow):
    revisions = re.findall(r"uses:\s+github/codeql-action/(\w+)@([^\s]+)", workflow)
    assert sorted(action for action, _ in revisions) == ["analyze", "init"]
    assert all(re.fullmatch(r"[0-9a-f]{40}", revision) for _, revision in revisions)
    assert len({revision for _, revision in revisions}) == 1, "CodeQL versions differ"


def test_committed_codeql_actions_are_pinned_and_aligned():
    workflow = (PROJECT_ROOT / ".github/workflows/codeql.yml").read_text()
    assert_codeql_actions_aligned(workflow)


@pytest.mark.parametrize("changed_action", ["init", "analyze"])
def test_codeql_policy_refuses_a_split_update(changed_action):
    workflow = "\n".join(
        f"uses: github/codeql-action/{action}@{'b' * 40 if action == changed_action else 'a' * 40}"
        for action in ("init", "analyze")
    )
    with pytest.raises(AssertionError, match="CodeQL versions differ"):
        assert_codeql_actions_aligned(workflow)


@pytest.mark.parametrize("revision", ["v4", "main", "9b32540"])
def test_codeql_policy_refuses_mutable_or_short_pins(revision):
    workflow = "\n".join(
        f"uses: github/codeql-action/{action}@{revision}" for action in ("init", "analyze")
    )
    with pytest.raises(AssertionError):
        assert_codeql_actions_aligned(workflow)
