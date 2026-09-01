"""Dataset Registry Module (TASK-21).

Tracks raw dataset provenance, SHA-256 checksums, row counts, and metadata.
Ensures reproducibility and auditability of every training run.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any

from ml_engine.config import RAW_DATA_DIR


_REGISTRY_FILE = RAW_DATA_DIR / "dataset_registry.json"


def compute_file_sha256(filepath: Path | str) -> str:
    """Compute SHA-256 checksum of a file in streaming chunks."""
    p = Path(filepath)
    if not p.exists():
        return ""
    sha256 = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


class DatasetRegistry:
    """JSON-backed registry that records every raw dataset used for training.

    Stored at ``data/raw/dataset_registry.json``.  Each entry captures:
    - ``name``: logical dataset name (e.g. ``"cell2cell_v1"``)
    - ``source``: ``"synthetic"`` | ``"kaggle"`` | ``"custom"``
    - ``path``: absolute path to the raw file
    - ``sha256``: hex digest of the raw file at registration time
    - ``row_count``: number of rows in the dataset
    - ``registered_at``: ISO-8601 UTC timestamp
    - ``notes``: free-text provenance notes
    """

    def __init__(self, registry_file: Path = _REGISTRY_FILE):
        self._registry_file = registry_file
        self._ensure_registry_file()

    def _ensure_registry_file(self) -> None:
        if not self._registry_file.exists():
            self._registry_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._registry_file, "w") as f:
                json.dump({"datasets": {}}, f, indent=2)

    def _load(self) -> dict[str, Any]:
        with open(self._registry_file, "r") as f:
            return json.load(f)

    def _save(self, data: dict[str, Any]) -> None:
        with open(self._registry_file, "w") as f:
            json.dump(data, f, indent=2)

    def register_dataset(
        self,
        name: str,
        path: Path | str,
        source: str,
        row_count: int,
        notes: str = "",
    ) -> dict[str, Any]:
        """Register a raw dataset, computing its SHA-256 checksum.

        Args:
            name: Logical name for the dataset (e.g. ``"cell2cell_v1"``).
            path: Absolute or relative path to the raw CSV / Parquet file.
            source: Data source tag: ``"synthetic"`` | ``"kaggle"`` | ``"custom"``.
            row_count: Number of rows in the dataset.
            notes: Optional provenance or download notes.

        Returns:
            The metadata dict that was written to the registry.
        """
        path = Path(path)
        sha256 = compute_file_sha256(path)

        entry: dict[str, Any] = {
            "name": name,
            "source": source,
            "path": str(path.resolve()),
            "sha256": sha256,
            "row_count": row_count,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "notes": notes,
        }

        data = self._load()
        data["datasets"][name] = entry
        self._save(data)

        print(
            f"[DatasetRegistry] Registered '{name}' | source={source} "
            f"| rows={row_count} | sha256={sha256[:12]}..."
        )
        return entry

    def get_dataset_info(self, name: str) -> dict[str, Any] | None:
        """Return metadata for a registered dataset, or None if not found."""
        data = self._load()
        return data["datasets"].get(name)

    def list_datasets(self) -> list[dict[str, Any]]:
        """Return a list of all registered dataset metadata dicts."""
        data = self._load()
        return list(data["datasets"].values())

    def verify_integrity(self, name: str) -> bool:
        """Verify the SHA-256 of a registered dataset matches the file on disk.

        Returns True if the checksum matches, False otherwise.
        """
        entry = self.get_dataset_info(name)
        if not entry:
            return False
        path = Path(entry["path"])
        if not path.exists():
            return False
        actual = compute_file_sha256(path)
        return actual == entry.get("sha256", "")
