"""Enumerations for all categorical fields.

All categoricals use explicit enums — no bare strings in business logic.
See PROJECT_CHARTER.md §6.4 Data Quality Rules.
"""

from enum import StrEnum


class TaskCategory(StrEnum):
    """Warehouse-relevant task taxonomy for UnifoLM-WBT episodes."""

    PICK_SMALL_OBJECT = "pick_small_object"
    PICK_MEDIUM_OBJECT = "pick_medium_object"
    PICK_LARGE_OBJECT = "pick_large_object"
    TRANSPORT_SHORT = "transport_short"
    TRANSPORT_LONG = "transport_long"
    PLACE_PRECISE = "place_precise"
    PLACE_GENERAL = "place_general"
    BIMANUAL_HANDLING = "bimanual_handling"
    UNCLASSIFIED = "unclassified"


class RobotPlatform(StrEnum):
    G1 = "G1"
    H1_2 = "H1_2"
    UNKNOWN = "unknown"


class AgentType(StrEnum):
    HUMAN = "human"
    HUMANOID = "humanoid"
    AMR = "amr"


class ScenarioId(StrEnum):
    BASELINE_HUMAN = "S-baseline-human"
    PURE_HUMANOID = "S-pure-humanoid"
    HYBRID_5050 = "S-hybrid-5050"
    HYBRID_AMR = "S-hybrid-amr"
    FUTURE_2028 = "S-future-2028"


class ArchitectureType(StrEnum):
    AUTOSTORE = "autostore"
    STINGRAY = "stingray"
    AUTOMOTIVE_LINE = "automotive_line"
