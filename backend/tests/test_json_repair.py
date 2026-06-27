# Daniel Design
import json

import pytest

from app.llm import repair_json


def test_plain_object():
    assert repair_json('{"a": 1}') == {"a": 1}


def test_surrounding_prose():
    assert repair_json("Here is the result: {\"a\": 1, \"b\": 2} done") == {"a": 1, "b": 2}


def test_strips_think_block():
    # Reasoning models wrap output in <think>; braces inside must not fool extraction.
    text = '<think>\nLet me reason {about this} carefully\n</think>\n{"agent": "code_audit", "score": 80}'
    assert repair_json(text) == {"agent": "code_audit", "score": 80}


def test_markdown_fence():
    text = '```json\n{"agent": "code_audit", "score": 80}\n```'
    assert repair_json(text) == {"agent": "code_audit", "score": 80}


def test_bare_fence():
    text = '```\n{"x": true}\n```'
    assert repair_json(text) == {"x": True}


def test_nested_and_arrays():
    text = 'noise {"dims": [1, 2, {"k": "v"}]} trailing'
    assert repair_json(text) == {"dims": [1, 2, {"k": "v"}]}


def test_invalid_raises():
    with pytest.raises(json.JSONDecodeError):
        repair_json("no json here at all !!!")
