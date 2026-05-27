"""Task taxonomy mapper for UnifoLM episodes.

Maps Unitree episodes to one or more warehouse-relevant TaskCategory values.
Real-world UnifoLM episodes carry the literal string "task" in their
`task` metadata field; the semantic signal lives in the dataset repo id
(e.g. `G1_WBT_Inspire_Pickup_Pillow_MainCamOnly`) and in the
`task_category_source` label from `config/dataset_manifest.yaml`.

`classify_task` returns a **list** of categories so an episode can be
counted under every category whose skill is exercised — placing clothes
into a washing machine is both PLACE_GENERAL and BIMANUAL_HANDLING.

See PROJECT_CHARTER.md §4 Module 1, Step 4.
"""

from __future__ import annotations

from warehouse_humanoid_tco.data.enums import TaskCategory

# Keyword rules: any substring match (after normalization) tags the episode
# with that category. An episode can match multiple categories.
TAXONOMY_KEYWORD_RULES: dict[str, list[str]] = {
    TaskCategory.BIMANUAL_HANDLING: [
        "both hands",
        "two hands",
        "bimanual",
        "dual arm",
        "dualarm",
        "two handed",
        "two-handed",
    ],
    TaskCategory.PICK_SMALL_OBJECT: [
        "pick up small",
        "grasp small",
        "pick the cup",
        "pick the bottle",
        "pick the pen",
        "pick the key",
        "small object",
    ],
    TaskCategory.PICK_LARGE_OBJECT: [
        "lift large",
        "carry large",
        "two-handed lift",
        "bimanual lift",
        "heavy",
        "box",
        "large object",
    ],
    TaskCategory.PICK_MEDIUM_OBJECT: [
        "pickup",
        "pick up",
        "pick the",
        "grasp",
        "lift",
        "take the",
        "grab",
        "pillow",
        "plate",
        "clothes",
    ],
    TaskCategory.TRANSPORT_LONG: [
        "walk to",
        "carry to",
        "navigate",
        "deliver",
        "carry across",
    ],
    TaskCategory.TRANSPORT_SHORT: [
        "move to",
        "place on",
        "transfer to",
        "hand over",
        "slide to",
        "collect",
        "into dishwasher",
        "into washing machine",
    ],
    TaskCategory.PLACE_PRECISE: [
        "place precisely",
        "insert",
        "slot",
        "align",
        "stack",
    ],
    TaskCategory.PLACE_GENERAL: [
        "drop",
        "release",
        "place in",
        "put in",
        "put clothes",
        "into washing machine",
        "into dishwasher",
    ],
}

# Author-labeled `task_category_source` from config/dataset_manifest.yaml.
# Maps to one or more TaskCategory enums. `manipulate_diverse` exercises a
# broad pick+place skill space and is intentionally tagged as both.
SOURCE_CATEGORY_MAP: dict[str, list[TaskCategory]] = {
    "pick_small": [TaskCategory.PICK_SMALL_OBJECT],
    "pick_medium": [TaskCategory.PICK_MEDIUM_OBJECT],
    "pick_large": [TaskCategory.PICK_LARGE_OBJECT],
    "place_general": [TaskCategory.PLACE_GENERAL],
    "place_precise": [TaskCategory.PLACE_PRECISE],
    "transport_short": [TaskCategory.TRANSPORT_SHORT],
    "transport_long": [TaskCategory.TRANSPORT_LONG],
    "bimanual_handling": [TaskCategory.BIMANUAL_HANDLING],
    "manipulate_diverse": [
        TaskCategory.PICK_MEDIUM_OBJECT,
        TaskCategory.PLACE_GENERAL,
    ],
}


def _normalize(text: str | None) -> str:
    if not text:
        return ""
    return text.lower().replace("_", " ").replace("-", " ")


def classify_task(
    description: str | None,
    dataset_repo_id: str | None = None,
    task_category_source: str | None = None,
) -> list[TaskCategory]:
    """Return all TaskCategory values an episode matches (multi-label).

    Signal sources in order of precedence:
      1. `task_category_source` — author-labeled manifest tag, most reliable.
      2. `dataset_repo_id` — rich semantic content in the dataset name
         (e.g. `G1_WBT_Inspire_Pickup_Pillow` → PICK_MEDIUM_OBJECT).
      3. `description` — often the literal "task" string in UnifoLM, but
         honored for completeness.

    Returns a deduplicated, ordered list. If nothing matches, returns
    `[TaskCategory.UNCLASSIFIED]` (never an empty list).
    """
    matched: list[TaskCategory] = []

    if task_category_source:
        for cat in SOURCE_CATEGORY_MAP.get(task_category_source, []):
            if cat not in matched:
                matched.append(cat)

    haystack = _normalize(dataset_repo_id) + " " + _normalize(description)
    for category, keywords in TAXONOMY_KEYWORD_RULES.items():
        for keyword in keywords:
            if _normalize(keyword) in haystack:
                cat_enum = TaskCategory(category)
                if cat_enum not in matched:
                    matched.append(cat_enum)
                break  # one keyword per category is enough

    return matched if matched else [TaskCategory.UNCLASSIFIED]


def needs_manual_review(
    description: str | None,
    dataset_repo_id: str | None = None,
    task_category_source: str | None = None,
) -> bool:
    """True iff the episode is UNCLASSIFIED across all signals."""
    return classify_task(description, dataset_repo_id, task_category_source) == [
        TaskCategory.UNCLASSIFIED
    ]
