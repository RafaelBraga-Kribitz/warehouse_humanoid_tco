"""Pytest configuration and shared fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_task_descriptions() -> list[str]:
    return [
        "pick up small cup from table",
        "pick up the box and carry it to the shelf",
        "walk to the other side of the room and place the item",
        "bimanual coordination to fold the cloth",
        "place precisely into the drawer slot",
        "drop the object into the container",
        "some completely unrelated description without keywords",
    ]
