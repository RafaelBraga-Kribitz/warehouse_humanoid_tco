"""Unit tests for data/download.py.

All HuggingFace network calls are mocked — no real HTTP requests are made.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from warehouse_humanoid_tco.data.download import (
    download_dataset,
    download_dataset_collection,
    resolve_revision_sha,
    sha256_file,
)

# ---------------------------------------------------------------------------
# resolve_revision_sha
# ---------------------------------------------------------------------------

FAKE_SHA = "abc123def456abc123def456abc123def456abc1"


def test_resolve_revision_sha_returns_sha() -> None:
    fake_info = SimpleNamespace(sha=FAKE_SHA)
    mock_api = MagicMock()
    mock_api.dataset_info.return_value = fake_info

    with patch("warehouse_humanoid_tco.data.download.HfApi", return_value=mock_api):
        result = resolve_revision_sha("org/dataset", revision="main")

    assert result == FAKE_SHA
    mock_api.dataset_info.assert_called_once_with(repo_id="org/dataset", revision="main")


def test_resolve_revision_sha_raises_when_sha_is_none() -> None:
    fake_info = SimpleNamespace(sha=None)
    mock_api = MagicMock()
    mock_api.dataset_info.return_value = fake_info

    with patch("warehouse_humanoid_tco.data.download.HfApi", return_value=mock_api):
        with pytest.raises(ValueError, match="Could not resolve SHA"):
            resolve_revision_sha("org/dataset", revision="main")


# ---------------------------------------------------------------------------
# download_dataset
# ---------------------------------------------------------------------------


def test_download_dataset_calls_snapshot_download(tmp_path: Path) -> None:
    local_dir = tmp_path / "datasets"
    local_dir.mkdir()
    expected_path = str(local_dir)

    with patch(
        "warehouse_humanoid_tco.data.download.snapshot_download",
        return_value=expected_path,
    ) as mock_snap:
        result = download_dataset("org/dataset", FAKE_SHA, local_dir)

    mock_snap.assert_called_once_with(
        repo_id="org/dataset",
        repo_type="dataset",
        revision=FAKE_SHA,
        local_dir=str(local_dir),
        token=None,
    )
    assert result == Path(expected_path)


def test_download_dataset_passes_token(tmp_path: Path) -> None:
    with patch(
        "warehouse_humanoid_tco.data.download.snapshot_download",
        return_value=str(tmp_path),
    ) as mock_snap:
        download_dataset("org/dataset", FAKE_SHA, tmp_path, token="hf_secret")

    _, kwargs = mock_snap.call_args
    assert kwargs["token"] == "hf_secret"


def test_download_dataset_rejects_main_as_revision(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pinned commit SHA"):
        download_dataset("org/dataset", "main", tmp_path)


def test_download_dataset_rejects_non_hex_sha(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="pinned commit SHA"):
        download_dataset("org/dataset", "not-a-sha", tmp_path)


# ---------------------------------------------------------------------------
# download_dataset_collection
# ---------------------------------------------------------------------------


def test_download_dataset_collection_processes_all_entries(tmp_path: Path) -> None:
    sha_a = "a" * 40
    sha_b = "b" * 40

    datasets = [
        {"repo_id": "org/dataset-a", "task_category": "pick", "phase": "train"},
        {"repo_id": "org/dataset-b"},
    ]

    def fake_resolve(repo_id: str, revision: str = "main") -> str:
        return sha_a if repo_id == "org/dataset-a" else sha_b

    def fake_download(
        repo_id: str, revision_sha: str, local_dir: Path, *, token: str | None = None
    ) -> Path:
        return local_dir

    with (
        patch(
            "warehouse_humanoid_tco.data.download.resolve_revision_sha",
            side_effect=fake_resolve,
        ),
        patch(
            "warehouse_humanoid_tco.data.download.download_dataset",
            side_effect=fake_download,
        ),
    ):
        provenance = download_dataset_collection(datasets, tmp_path)

    assert set(provenance.keys()) == {"org/dataset-a", "org/dataset-b"}
    assert provenance["org/dataset-a"]["sha"] == sha_a
    assert provenance["org/dataset-a"]["task_category"] == "pick"
    assert provenance["org/dataset-a"]["phase"] == "train"
    assert provenance["org/dataset-b"]["task_category"] is None
    assert provenance["org/dataset-b"]["phase"] is None


def test_download_dataset_collection_uses_dataset_name_as_subdir(tmp_path: Path) -> None:
    sha = "c" * 40
    datasets = [{"repo_id": "myorg/my-dataset"}]

    captured_dirs: list[Path] = []

    def fake_download(
        repo_id: str, revision_sha: str, local_dir: Path, *, token: str | None = None
    ) -> Path:
        captured_dirs.append(local_dir)
        return local_dir

    with (
        patch(
            "warehouse_humanoid_tco.data.download.resolve_revision_sha",
            return_value=sha,
        ),
        patch(
            "warehouse_humanoid_tco.data.download.download_dataset",
            side_effect=fake_download,
        ),
    ):
        download_dataset_collection(datasets, tmp_path)

    assert len(captured_dirs) == 1
    assert captured_dirs[0] == tmp_path / "my-dataset"


# ---------------------------------------------------------------------------
# sha256_file
# ---------------------------------------------------------------------------


def test_sha256_file_known_content(tmp_path: Path) -> None:
    content = b"warehouse humanoid tco test content"
    test_file = tmp_path / "sample.bin"
    test_file.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    assert sha256_file(test_file) == expected


def test_sha256_file_empty_file(tmp_path: Path) -> None:
    empty_file = tmp_path / "empty.bin"
    empty_file.write_bytes(b"")

    expected = hashlib.sha256(b"").hexdigest()
    assert sha256_file(empty_file) == expected


def test_sha256_file_large_content(tmp_path: Path) -> None:
    # > 65536 bytes to exercise the chunked read path
    content = b"x" * (65536 * 3)
    large_file = tmp_path / "large.bin"
    large_file.write_bytes(content)

    expected = hashlib.sha256(content).hexdigest()
    assert sha256_file(large_file) == expected
