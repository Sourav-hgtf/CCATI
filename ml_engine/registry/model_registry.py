"""Model Registry Module (TICKET-207).

Manages model artifact persistence (.joblib/.pkl), SHA-256 checksums, and metadata versioning.
"""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
import joblib
from ml_engine.config import MODEL_REGISTRY_DIR


def compute_file_sha256(filepath: Path | str) -> str:
    """Compute SHA-256 checksum hash of a binary file."""
    p = Path(filepath)
    if not p.exists():
        return ""
    sha256 = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


class ModelRegistry:
    """Artifact storage, SHA-256 checksum verification, and versioning registry for trained ML models."""

    def __init__(self, registry_dir: Path = MODEL_REGISTRY_DIR):
        self.registry_dir = registry_dir
        self.metadata_file = self.registry_dir / "registry_metadata.json"
        self._ensure_metadata_file()

    def _ensure_metadata_file(self):
        if not self.metadata_file.exists():
            self.registry_dir.mkdir(parents=True, exist_ok=True)
            with open(self.metadata_file, "w") as f:
                json.dump({"models": {}, "promoted_version": None}, f, indent=2)

    def _load_metadata(self) -> dict[str, Any]:
        with open(self.metadata_file, "r") as f:
            return json.load(f)

    def _save_metadata(self, meta: dict[str, Any]):
        with open(self.metadata_file, "w") as f:
            json.dump(meta, f, indent=2)

    def register_model(
        self,
        model: Any,
        model_name: str,
        version: str,
        metrics: dict[str, Any],
        feature_names: list[str],
        hyperparameters: dict[str, Any],
        promote: bool = False,
    ) -> str:
        """Register a trained model artifact, SHA-256 checksum, and its metadata."""
        artifact_filename = f"{model_name}_{version}.joblib"
        artifact_path = self.registry_dir / artifact_filename

        # Save artifact
        joblib.dump(model, artifact_path)
        sha256_hash = compute_file_sha256(artifact_path)

        meta = self._load_metadata()
        meta["models"][version] = {
            "model_name": model_name,
            "version": version,
            "artifact_path": str(artifact_path),
            "sha256": sha256_hash,
            "registered_at": datetime.now(timezone.utc).isoformat(),
            "metrics": metrics,
            "feature_names": feature_names,
            "hyperparameters": hyperparameters,
            "status": "PROMOTED" if promote else "CANDIDATE",
        }

        if promote:
            # Demote previously promoted models
            for v, m_info in meta["models"].items():
                if v != version and m_info.get("status") == "PROMOTED":
                    m_info["status"] = "CANDIDATE"
            meta["promoted_version"] = version

        self._save_metadata(meta)
        return version

    def get_model(self, version: str | None = None) -> tuple[Any, dict[str, Any]]:
        """Retrieve model object and metadata by version or latest promoted."""
        meta = self._load_metadata()

        if version is None:
            version = meta.get("promoted_version")
            if version is None and meta["models"]:
                # Default to latest registered version if none promoted yet
                version = list(meta["models"].keys())[-1]

        if not version or version not in meta["models"]:
            raise ValueError(f"Model version '{version}' not found in registry.")

        m_info = meta["models"][version]
        art_path = Path(m_info["artifact_path"])
        if not art_path.exists():
            raise FileNotFoundError(f"Model artifact file '{art_path}' missing from disk.")

        model = joblib.load(art_path)
        return model, m_info

    def get_active_model_info(self) -> dict[str, Any]:
        """Retrieve metadata dictionary for active production model."""
        meta = self._load_metadata()
        version = meta.get("promoted_version")
        if not version and meta["models"]:
            version = list(meta["models"].keys())[-1]
        if not version or version not in meta["models"]:
            raise ValueError("No active model found in registry.")
        return meta["models"][version]

    def verify_integrity(self, version: str | None = None) -> bool:
        """Verify SHA-256 checksum and artifact presence for specified version or active model."""
        meta = self._load_metadata()
        if version is None:
            version = meta.get("promoted_version")
            if version is None and meta["models"]:
                version = list(meta["models"].keys())[-1]

        if not version or version not in meta["models"]:
            return False

        m_info = meta["models"][version]
        art_path = Path(m_info["artifact_path"])
        if not art_path.exists():
            return False

        expected_hash = m_info.get("sha256")
        if expected_hash:
            actual_hash = compute_file_sha256(art_path)
            return actual_hash == expected_hash

        return True

    def list_models(self) -> list[dict[str, Any]]:
        """List all registered models and metadata."""
        meta = self._load_metadata()
        return list(meta["models"].values())

    def promote_model(self, version: str) -> dict[str, Any]:
        """Promote a specific model version to production."""
        meta = self._load_metadata()
        if version not in meta["models"]:
            raise ValueError(f"Version '{version}' not found.")

        for v, m_info in meta["models"].items():
            m_info["status"] = "PROMOTED" if v == version else "CANDIDATE"

        meta["promoted_version"] = version
        self._save_metadata(meta)
        return meta["models"][version]
