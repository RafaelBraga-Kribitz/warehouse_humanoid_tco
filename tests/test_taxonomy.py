"""Unit tests for the task taxonomy mapper."""

from __future__ import annotations

import pytest

from warehouse_humanoid_tco.data.enums import TaskCategory
from warehouse_humanoid_tco.features.taxonomy import classify_task, needs_manual_review


def test_classify_small_object() -> None:
    result = classify_task("pick up small cup from table")
    assert result == TaskCategory.PICK_SMALL_OBJECT


def test_classify_transport_long() -> None:
    result = classify_task("walk to the shelf and place the item")
    assert result == TaskCategory.TRANSPORT_LONG


def test_classify_bimanual() -> None:
    result = classify_task("use both hands to fold the cloth")
    assert result == TaskCategory.BIMANUAL_HANDLING


def test_classify_empty_string() -> None:
    result = classify_task("")
    assert result == TaskCategory.UNCLASSIFIED


def test_classify_none_like_input() -> None:
    result = classify_task("completely unrelated text with no keywords here")
    assert result == TaskCategory.UNCLASSIFIED


def test_needs_manual_review_true() -> None:
    assert needs_manual_review("something completely unknown") is True


def test_needs_manual_review_false() -> None:
    assert needs_manual_review("pick up small cup") is False
