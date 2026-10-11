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
    """Business-readable scenario names (F-242).

    The string value is the identifier used everywhere: config, JSON, CSV,
    chart labels, and prose. Never reintroduce the retired ``S-...`` codes.
    """

    LEGACY_OVERSTAFFED_TEAM = "Legacy Overstaffed Team"
    LEAN_HUMAN_TEAM = "Lean Human Team"
    LEAN_HUMAN_AMR_TEAM = "Lean Human + AMR Team"
    ALL_HUMANOID_TEAM = "All-Humanoid Team"
    HALF_HUMAN_HALF_HUMANOID_TEAM = "Half Human + Half Humanoid Team"
    HUMAN_HUMANOID_AMR_TEAM = "Human + Humanoid + AMR Team"
    FUTURE_2028_HUMANOID_TEAM = "Future 2028 Humanoid Team"


class ArchitectureType(StrEnum):
    AUTOSTORE = "autostore"
    STINGRAY = "stingray"
    AUTOMOTIVE_LINE = "automotive_line"
