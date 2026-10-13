"""Data validation and quality profiling for CSV sales datasets."""

from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from pydantic import BaseModel, Field

from businessinsight.config import settings
from businessinsight.data.column_mapping import ColumnMapper


class DataQualitySummary(BaseModel):
    """Summary of data-quality metrics and issues."""

    total_rows: int
    total_columns: int
    duplicate_rows: int
    missing_values_by_column: Dict[str, int]
    negative_sales_rows: int = 0
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    critical_errors: List[str] = Field(default_factory=list)
    is_valid_for_analysis: bool = True


class DatasetProfile(BaseModel):
    """Structured data profile produced by dataset inspection."""

    file_path: str
    file_size_bytes: int
    detected_encoding: str
    column_names: List[str]
    column_mapping: Dict[str, str]
    missing_required_fields: List[str]
    quality_summary: DataQualitySummary
    preview_sample: List[Dict[str, Any]] = Field(default_factory=list)


def validate_file_safety(file_path: Path) -> None:
    """Deterministic validation of file path and size before loading."""
    if not file_path.exists():
        raise FileNotFoundError(
            f"Dataset file not found at '{file_path}'. "
            f"Please download the dataset from Kaggle and place it at '{settings.dataset_path}'."
        )

    if not file_path.is_file():
        raise ValueError(f"Target path '{file_path}' is not a regular file.")


    if file_path.suffix.lower() != ".csv":
        raise ValueError(f"Unsupported file format '{file_path.suffix}'. Only CSV files are supported.")


    file_size = file_path.stat().st_size
    if file_size > settings.max_csv_bytes:
        max_mb = settings.max_csv_bytes / (1024 * 1024)
        actual_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"Dataset file size ({actual_mb:.1f} MB) exceeds maximum allowed limit ({max_mb:.0f} MB)."
        )


def validate_and_profile_dataframe(df: pd.DataFrame, file_path: Path, mapping: Dict[str, str]) -> DatasetProfile:
    """Performs deterministic schema and data quality validation on the loaded DataFrame."""
    total_rows = len(df)
    total_cols = len(df.columns)
    warnings: List[str] = []
    critical_errors: List[str] = []


    if total_rows == 0:
        critical_errors.append("Dataset contains 0 rows.")


    missing_required = ColumnMapper.get_missing_required_fields(mapping)
    if missing_required:
        critical_errors.append(
            f"Missing required canonical fields: {', '.join(missing_required)}. "
            f"Available columns: {', '.join(df.columns)}"
        )


    missing_by_col = {col: int(df[col].isna().sum()) for col in df.columns}
    for col, count in missing_by_col.items():
        if count > 0:
            pct = (count / total_rows) * 100 if total_rows > 0 else 0
            if pct > 10.0:
                warnings.append(f"Column '{col}' has {count} missing values ({pct:.1f}%).")


    duplicates = int(df.duplicated().sum())
    if duplicates > 0:
        warnings.append(f"Found {duplicates} duplicate rows in dataset.")


    negative_sales = 0
    if "sales" in mapping and mapping["sales"] in df.columns:
        sales_col = mapping["sales"]
        try:
            numeric_sales = pd.to_numeric(df[sales_col], errors="coerce")
            nan_sales = int(numeric_sales.isna().sum())
            if nan_sales > 0:
                warnings.append(f"Found {nan_sales} non-numeric sales values in '{sales_col}'.")
            negative_sales = int((numeric_sales < 0).sum())
            if negative_sales > 0:
                warnings.append(
                    f"Found {negative_sales} negative sales values in '{sales_col}'. "
                    "These may represent returns or refunds."
                )
        except Exception as e:
            critical_errors.append(f"Failed to parse sales column '{sales_col}': {e}")


    date_start_str = None
    date_end_str = None
    if "order_date" in mapping and mapping["order_date"] in df.columns:
        date_col = mapping["order_date"]
        try:
            parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
            invalid_dates = int(parsed_dates.isna().sum())
            if invalid_dates > 0:
                warnings.append(f"Found {invalid_dates} unparseable dates in '{date_col}'.")
            valid_dates = parsed_dates.dropna()
            if not valid_dates.empty:
                date_start_str = valid_dates.min().strftime("%Y-%m-%d")
                date_end_str = valid_dates.max().strftime("%Y-%m-%d")
        except Exception as e:
            critical_errors.append(f"Failed to parse date column '{date_col}': {e}")


    for col in df.select_dtypes(include=["object"]).columns:

        formula_triggers = df[col].astype(str).str.startswith(("=", "@", "\t", "\r")).sum()
        if formula_triggers > 0:
            warnings.append(f"Column '{col}' contains {formula_triggers} values with potential formula prefixes.")

    is_valid = len(critical_errors) == 0

    quality_summary = DataQualitySummary(
        total_rows=total_rows,
        total_columns=total_cols,
        duplicate_rows=duplicates,
        missing_values_by_column=missing_by_col,
        negative_sales_rows=negative_sales,
        date_range_start=date_start_str,
        date_range_end=date_end_str,
        warnings=warnings,
        critical_errors=critical_errors,
        is_valid_for_analysis=is_valid,
    )


    preview = df.head(5).to_dict(orient="records")

    preview_serializable = []
    for row in preview:
        preview_serializable.append({k: str(v) if pd.notna(v) else None for k, v in row.items()})

    return DatasetProfile(
        file_path=str(file_path),
        file_size_bytes=file_path.stat().st_size if file_path.exists() else 0,
        detected_encoding="utf-8",
        column_names=list(df.columns),
        column_mapping=mapping,
        missing_required_fields=missing_required,
        quality_summary=quality_summary,
        preview_sample=preview_serializable,
    )
