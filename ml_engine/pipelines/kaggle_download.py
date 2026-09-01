"""Secure Kaggle Dataset Download Module (TASK-21).

Handles Kaggle API authentication via environment variables or .kaggle/kaggle.json
without hardcoding credentials. Downloads the Cell2Cell dataset securely.
"""

import os
from pathlib import Path
from typing import Optional
import json


def ensure_kaggle_credentials() -> bool:
    """Verify Kaggle credentials are available (env vars or .kaggle/kaggle.json).
    
    Returns:
        True if credentials are found, False otherwise.
    """
    # Check environment variables
    if os.environ.get("KAGGLE_USERNAME") and os.environ.get("KAGGLE_KEY"):
        return True
    
    # Check .kaggle/kaggle.json
    kaggle_json = Path.home() / ".kaggle" / "kaggle.json"
    if kaggle_json.exists():
        return True
    
    return False


def download_kaggle_dataset(
    dataset_name: str = "aryafar/cell2cell-telecom-churn",
    output_path: Optional[Path] = None,
) -> Optional[Path]:
    """Download a Kaggle dataset using secure credentials.
    
    Credentials are retrieved from:
    1. KAGGLE_USERNAME and KAGGLE_KEY environment variables
    2. ~/.kaggle/kaggle.json file (from official Kaggle CLI)
    
    Args:
        dataset_name: Kaggle dataset identifier (owner/dataset).
        output_path: Directory to download into. Defaults to data/raw/.
    
    Returns:
        Path to the downloaded file, or None if download fails.
    
    Raises:
        ImportError: If kaggle-api is not installed.
        RuntimeError: If credentials are not found.
    """
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        raise ImportError(
            "kaggle library is not installed. Install with: pip install kaggle"
        )
    
    if not ensure_kaggle_credentials():
        raise RuntimeError(
            "Kaggle credentials not found. Ensure KAGGLE_USERNAME and KAGGLE_KEY "
            "environment variables are set, or place credentials in ~/.kaggle/kaggle.json"
        )
    
    if output_path is None:
        from ml_engine.config import RAW_DATA_DIR
        output_path = RAW_DATA_DIR
    
    output_path = Path(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Authenticate using the Kaggle API
    api = KaggleApi()
    api.authenticate()
    
    print(f"Downloading Kaggle dataset: {dataset_name}")
    api.dataset_download_files(dataset_name, path=str(output_path), unzip=True)
    print(f"Dataset downloaded to: {output_path}")
    
    # Find and return the main CSV file
    csv_files = list(output_path.glob("*.csv"))
    if csv_files:
        return csv_files[0]
    
    return None


def download_cell2cell_dataset(
    output_path: Optional[Path] = None,
) -> Optional[Path]:
    """Download the Cell2Cell Kaggle dataset specifically.
    
    Args:
        output_path: Directory to download into. Defaults to data/raw/.
    
    Returns:
        Path to the downloaded Cell2Cell CSV file.
    """
    return download_kaggle_dataset(
        dataset_name="aryafar/cell2cell-telecom-churn",
        output_path=output_path,
    )
