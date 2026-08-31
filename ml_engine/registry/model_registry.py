"""Model Registry Module (TICKET-207).

Manages model artifact persistence (.joblib/.pkl) and metadata versioning.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any
import joblib
from ml_engine.config import MODEL_REGISTRY_DIR


class ModelRegistry:
    """Artifact storage and versioning registry for trained ML models."""

    def __init__(self, registry_dir: Path = MODEL_REGISTRY_DIR):
        self.registry_dir = registry_dir
        self.metadata_file = self.registry_dir / "registry_metadata.json"
        self._ensure_metadata_file()

    def _ensure_metadata_file(self):
        if not self.metadata_file.exists():
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
        """Register a trained model artifact and its metadata."""
        artifact_filename = f"{model_name}_{version}.joblib"
        artifact_path = self.registry_dir / artifact_filename
        
        # Save artifact
        joblib.dump(model, artifact_path)

        meta = self._load_metadata()
        meta["models"][version] = {
            "model_name": model_name,
            "version": version,
            "artifact_path": str(artifact_path),
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
        model = joblib.load(m_info["artifact_path"])
        return model, m_info

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
