"""Task taxonomy mapper for UnifoLM-WBT episodes.

Maps free-form Unitree task descriptions to the warehouse-relevant taxonomy.
See PROJECT_CHARTER.md §4 Module 1, Step 4 for the classification methodology.
"""

from __future__ import annotations

from warehouse_humanoid_tco.data.enums import TaskCategory

# Rules-based keyword mapping.
# Keys: TaskCategory values. Values: list of lowercase match strings.
# Order matters: first match wins for non-ambiguous cases.
TAXONOMY_KEYWORD_RULES: dict[str, list[str]] = {
    TaskCategory.BIMANUAL_HANDLING: [
        "both hands", "two hands", "bimanual", "dual arm",
    ],
    TaskCategory.PICK_SMALL_OBJECT: [
        "pick up small", "grasp small", "pick the cup", "pick the bottle",
        "pick the pen", "pick the key",
    ],
    TaskCategory.PICK_LARGE_OBJECT: [
        "lift large", "carry large", "two-handed lift", "bimanual lift",
        "heavy", "box",
    ],
    TaskCategory.PICK_MEDIUM_OBJECT: [
        "pick up", "grasp", "lift", "take the", "grab",
    ],
    TaskCategory.TRANSPORT_LONG: [
        "walk to", "carry to", "navigate", "deliver", "carry across",
    ],
    TaskCategory.TRANSPORT_SHORT: [
        "move to", "place on", "transfer to", "hand over", "slide to",
    ],
    TaskCategory.PLACE_PRECISE: [
        "place precisely", "insert", "slot", "align", "stack",
    ],
    TaskCategory.PLACE_GENERAL: [
        "drop", "release", "place in", "put in",
    ],
}


def classify_task(description: str) -> TaskCategory:
    """Map a task description string to a TaskCategory.

    Returns TaskCategory.UNCLASSIFIED when no rule matches or multiple rules
    conflict. Caller is responsible for routing ambiguous episodes to manual review.
    """
    if not description:
        return TaskCategory.UNCLASSIFIED

    desc_lower = description.lower()
    matches: list[str] = []

    for category, keywords in TAXONOMY_KEYWORD_RULES.items():
        for keyword in keywords:
            if keyword in desc_lower:
                matches.append(category)
                break

    if len(matches) == 1:
        return TaskCategory(matches[0])
    return TaskCategory.UNCLASSIFIED


def needs_manual_review(description: str) -> bool:
    """True if the episode cannot be cleanly classified by rules alone."""
    desc_lower = description.lower() if description else ""
    matches: list[str] = []
    for category, keywords in TAXONOMY_KEYWORD_RULES.items():
        for keyword in keywords:
            if keyword in desc_lower:
                matches.append(category)
                break
    return len(matches) != 1
