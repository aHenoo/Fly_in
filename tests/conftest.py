"""Shared fixtures and helpers for the Fly-in test suite."""

from pathlib import Path

import pytest

from src.parser.parser import ParsedMap, Parser


ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "maps"


@pytest.fixture
def parser() -> Parser:
    """Return a fresh parser for each test."""
    return Parser()


def parse_map(content: str) -> ParsedMap:
    """Parse an inline map after removing test indentation."""
    return Parser().parse_text(content)
