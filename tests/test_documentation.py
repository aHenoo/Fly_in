"""Checks for evaluation requirements that are documented rather than run."""

from conftest import ROOT


def test_readme_contains_required_sections_and_first_line() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    first_line = readme.splitlines()[0]

    expected = (
        "*This project has been created as part of the 42 curriculum "
        "by aheno.*"
    )
    assert first_line == expected
    for section in (
        "## Description",
        "## Instructions",
        "## Example",
        "## Algorithm and Implementation Strategy",
        "## Visual Representation",
        "## Resources",
        "### Use of AI",
        "### Complexity",
    ):
        assert section in readme


def test_algorithm_choices_are_documented() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
    for concept in (
        "dijkstra",
        "priority queue",
        "candidate path",
        "capacity",
        "restricted",
        "blocked",
        "complexity",
        "trade",
    ):
        assert concept in readme
