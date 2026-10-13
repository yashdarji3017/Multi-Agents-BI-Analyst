"""Profiling and schema validation analytical functions."""

from pathlib import Path
from typing import Optional, Tuple
import pandas as pd

from businessinsight.data.loader import DataLoader
from businessinsight.data.validators import DatasetProfile


def profile_dataset(dataset_path: Optional[Path] = None) -> DatasetProfile:
    """Profiles the sales dataset and returns complete data profile."""
    loader = DataLoader(dataset_path=dataset_path)
    _, profile = loader.load_canonical()
    return profile


def validate_sales_schema(df: pd.DataFrame) -> Tuple[bool, list[str]]:
    """Checks if the dataframe contains the required columns for sales intelligence.

    Returns (is_valid, missing_or_invalid_reasons).
    """
    required_cols = ["order_id", "order_date", "sales", "product_name", "category", "region"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        return False, [f"Missing required canonical column: {col}" for col in missing]
    return True, []
