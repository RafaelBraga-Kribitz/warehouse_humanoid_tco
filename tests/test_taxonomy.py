"""Unit tests for the multi-label task taxonomy mapper."""

from __future__ import annotations

from warehouse_humanoid_tco.data.enums import TaskCategory
from warehouse_humanoid_tco.features.taxonomy import classify_task, needs_manual_review


def test_classify_small_object_via_description() -> None:
    result = classify_task("pick up small cup from table")
    assert TaskCategory.PICK_SMALL_OBJECT in result


def test_classify_transport_long() -> None:
    result = classify_task("walk to the shelf and place the item")
    assert TaskCategory.TRANSPORT_LONG in result


def test_classify_bimanual() -> None:
    result = classify_task("use both hands to fold the cloth")
    assert TaskCategory.BIMANUAL_HANDLING in result


def test_classify_empty_string() -> None:
    result = classify_task("")
    assert result == [TaskCategory.UNCLASSIFIED]


def test_classify_none_like_input() -> None:
    result = classify_task("completely unrelated text with no keywords here")
    assert result == [TaskCategory.UNCLASSIFIED]


def test_classify_returns_list() -> None:
    """API contract: classify_task always returns a non-empty list."""
    result = classify_task("pick up small cup")
    assert isinstance(result, list)
    assert len(result) >= 1


def test_classify_multi_label_from_dataset_name() -> None:
    """Real UnifoLM data: episode `task` field is literally 'task'; signal
    comes from the dataset repo id."""
    result = classify_task(
        description="task",
        dataset_repo_id="unitreerobotics/G1_WBT_Inspire_Put_Clothes_into_Washing_Machine_MainCamOnly",
    )
    # Should detect both PLACE_GENERAL (put clothes / into washing machine) and
    # PICK_MEDIUM_OBJECT (clothes)
    assert TaskCategory.PLACE_GENERAL in result
    assert TaskCategory.PICK_MEDIUM_OBJECT in result


def test_classify_multi_label_dual_arm() -> None:
    result = classify_task(
        description="task",
        dataset_repo_id="unitreerobotics/G1_Dex1_DiverseManip_DualArm_256x256",
        task_category_source="manipulate_diverse",
    )
    # Dual arm → BIMANUAL_HANDLING; manipulate_diverse → PICK + PLACE
    assert TaskCategory.BIMANUAL_HANDLING in result
    assert TaskCategory.PICK_MEDIUM_OBJECT in result
    assert TaskCategory.PLACE_GENERAL in result


def test_classify_manifest_source_drives_classification() -> None:
    """When only the manifest tag is available, it still classifies."""
    result = classify_task(
        description="task",
        dataset_repo_id=None,
        task_category_source="pick_medium",
    )
    assert TaskCategory.PICK_MEDIUM_OBJECT in result
    assert TaskCategory.UNCLASSIFIED not in result


def test_classify_pickup_pillow_dataset() -> None:
    result = classify_task(
        description="task",
        dataset_repo_id="unitreerobotics/G1_WBT_Inspire_Pickup_Pillow_MainCamOnly",
        task_category_source="pick_medium",
    )
    assert TaskCategory.PICK_MEDIUM_OBJECT in result


def test_classify_dishwasher_dataset() -> None:
    result = classify_task(
        description="task",
        dataset_repo_id="unitreerobotics/G1_WBT_Brainco_Collect_Plates_Into_Dishwasher",
        task_category_source="place_general",
    )
    assert TaskCategory.PLACE_GENERAL in result
    assert TaskCategory.TRANSPORT_SHORT in result  # 'collect' / 'into dishwasher'
    assert TaskCategory.PICK_MEDIUM_OBJECT in result  # 'plate'


def test_classify_no_duplicates() -> None:
    """Same category matched by multiple sources should appear only once."""
    result = classify_task(
        description="pick up the pillow",
        dataset_repo_id="G1_WBT_Pickup_Pillow",
        task_category_source="pick_medium",
    )
    # PICK_MEDIUM_OBJECT triggered by all three sources
    assert result.count(TaskCategory.PICK_MEDIUM_OBJECT) == 1


def test_classify_none_arguments_safe() -> None:
    result = classify_task(None, None, None)
    assert result == [TaskCategory.UNCLASSIFIED]


def test_needs_manual_review_true() -> None:
    assert needs_manual_review("something completely unknown") is True


def test_needs_manual_review_false_via_description() -> None:
    assert needs_manual_review("pick up small cup") is False


def test_needs_manual_review_false_via_dataset_id() -> None:
    """Even with no description signal, dataset id alone unblocks review."""
    assert (
        needs_manual_review(
            description="task",
            dataset_repo_id="G1_WBT_Pickup_Pillow",
        )
        is False
    )
