"""Deterministic CSV loading and canonicalization."""

from pathlib import Path
from typing import Optional, Tuple
import pandas as pd

from businessinsight.config import settings
from businessinsight.data.column_mapping import ColumnMapper
from businessinsight.data.validators import (
    DatasetProfile,
    validate_and_profile_dataframe,
    validate_file_safety,
)


SUPPORTED_ENCODINGS = ["utf-8", "windows-1252", "latin1", "iso-8859-1"]


class DataLoader:
    """Safely loads CSV datasets into Pandas DataFrames and canonicalizes schema."""

    def __init__(self, dataset_path: Optional[Path] = None):
        self.dataset_path = dataset_path or settings.dataset_path
        self._raw_df: Optional[pd.DataFrame] = None
        self._canonical_df: Optional[pd.DataFrame] = None
        self._profile: Optional[DatasetProfile] = None

    def load_raw(self, force_reload: bool = False) -> Tuple[pd.DataFrame, str]:
        """Loads the raw CSV file into a Pandas DataFrame, testing safe encodings.

        Returns (df, detected_encoding).
        """
        if self._raw_df is not None and not force_reload:
            encoding = self._profile.detected_encoding if self._profile else "utf-8"
            return self._raw_df, encoding

        validate_file_safety(self.dataset_path)

        last_error = None
        for enc in SUPPORTED_ENCODINGS:
            try:

                df = pd.read_csv(self.dataset_path, encoding=enc, low_memory=False)
                self._raw_df = df
                return df, enc
            except (UnicodeDecodeError, UnicodeError) as e:
                last_error = e
                continue
            except Exception as e:
                raise ValueError(f"Failed to read CSV at '{self.dataset_path}': {e}") from e

        raise ValueError(
            f"Unable to read CSV with supported encodings {SUPPORTED_ENCODINGS}. Last error: {last_error}"
        )

    def load_canonical(self, force_reload: bool = False) -> Tuple[pd.DataFrame, DatasetProfile]:
        """Loads the CSV and converts it into a standardized canonical DataFrame.

        Returns (canonical_df, dataset_profile).
        """
        if self._canonical_df is not None and self._profile is not None and not force_reload:
            return self._canonical_df, self._profile

        raw_df, detected_enc = self.load_raw(force_reload=force_reload)


        mapping = ColumnMapper.detect_mapping(list(raw_df.columns))


        profile = validate_and_profile_dataframe(raw_df, self.dataset_path, mapping)
        profile.detected_encoding = detected_enc
        self._profile = profile

        if not profile.quality_summary.is_valid_for_analysis:
            error_msg = "; ".join(profile.quality_summary.critical_errors)
            raise ValueError(f"Dataset validation failed: {error_msg}")


        canonical_data = {}
        for canonical_key, raw_col in mapping.items():
            if raw_col in raw_df.columns:
                canonical_data[canonical_key] = raw_df[raw_col].copy()

        cdf = pd.DataFrame(canonical_data)


        if "order_date" in cdf.columns:
            cdf["order_date"] = pd.to_datetime(cdf["order_date"], errors="coerce")

            cdf = cdf.dropna(subset=["order_date"])

        if "sales" in cdf.columns:
            cdf["sales"] = pd.to_numeric(cdf["sales"], errors="coerce").fillna(0.0)

        if "quantity" in cdf.columns:
            cdf["quantity"] = pd.to_numeric(cdf["quantity"], errors="coerce").fillna(1)

        if "discount" in cdf.columns:
            cdf["discount"] = pd.to_numeric(cdf["discount"], errors="coerce").fillna(0.0)

        if "profit" in cdf.columns:
            cdf["profit"] = pd.to_numeric(cdf["profit"], errors="coerce").fillna(0.0)


        for str_col in ["order_id", "product_name", "category", "region", "segment", "sub_category"]:
            if str_col in cdf.columns:
                cdf[str_col] = cdf[str_col].astype(str).str.strip()


        if "order_date" in cdf.columns:
            cdf["year"] = cdf["order_date"].dt.year
            cdf["quarter"] = cdf["order_date"].dt.to_period("Q").astype(str)
            cdf["year_month"] = cdf["order_date"].dt.strftime("%Y-%m")

        self._canonical_df = cdf
        return cdf, profile


def load_superstore_data(
    dataset_path: Optional[Path] = None, force_reload: bool = False
) -> Tuple[pd.DataFrame, DatasetProfile]:
    """Helper to load and profile superstore data."""
    loader = DataLoader(dataset_path=dataset_path)
    return loader.load_canonical(force_reload=force_reload)
