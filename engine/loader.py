"""CSV ingestion, validation, and schema parsing."""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

REQUIRED_RECIPIENT_COLS = {"recipient_id", "full_name", "award_amount"}
REQUIRED_SCHOLARSHIP_COLS = {"scholarship_id", "name", "amount"}
CRIT_PATTERN = re.compile(r"^crit__(\w+)__(eq|gte|lte|contains)__(.+)$")


@dataclass
class Criterion:
    attribute: str
    operator: str  # eq | gte | lte | contains
    value: str
    column: str    # original column name, for error reporting


@dataclass
class LoadResult:
    recipients: pd.DataFrame
    scholarships: pd.DataFrame
    scholarship_criteria: dict[str, list[Criterion]]  # scholarship_id -> criteria list
    warnings: list[str] = field(default_factory=list)


def load_recipients(source: str | bytes | io.IOBase) -> pd.DataFrame:
    """Load and validate recipients CSV. Returns DataFrame indexed by recipient_id."""
    df = _read_csv(source)
    missing = REQUIRED_RECIPIENT_COLS - set(df.columns)
    if missing:
        raise ValueError(f"recipients CSV missing required columns: {sorted(missing)}")

    df["recipient_id"] = df["recipient_id"].astype(str).str.strip()
    df["award_amount"] = pd.to_numeric(df["award_amount"], errors="raise")

    invalid = df["award_amount"][~np.isfinite(df["award_amount"]) | (df["award_amount"] <= 0)]
    if not invalid.empty:
        raise ValueError(f"award_amount must be positive and finite; bad rows: {list(invalid.index)}")

    # Lowercase attribute columns for consistent criterion matching.
    # Preserve display columns (full_name) as-is.
    display_cols = {"recipient_id", "award_amount", "full_name"}
    for col in df.columns:
        if col not in display_cols:
            df[col] = df[col].astype(str).str.strip().str.lower()

    df = df.set_index("recipient_id")

    if not df.index.is_unique:
        dupes = list(df.index[df.index.duplicated()])
        raise ValueError(f"Duplicate recipient_id values: {dupes}")

    return df


def load_scholarships(source: str | bytes | io.IOBase) -> tuple[pd.DataFrame, dict[str, list[Criterion]], list[str]]:
    """Load and validate scholarships CSV.

    Returns:
        scholarships DataFrame indexed by scholarship_id,
        criteria dict mapping scholarship_id -> list of active Criterion,
        list of warnings
    """
    df = _read_csv(source)
    missing = REQUIRED_SCHOLARSHIP_COLS - set(df.columns)
    if missing:
        raise ValueError(f"scholarships CSV missing required columns: {sorted(missing)}")

    df["scholarship_id"] = df["scholarship_id"].astype(str).str.strip()
    df["amount"] = pd.to_numeric(df["amount"], errors="raise")

    invalid = df["amount"][~np.isfinite(df["amount"]) | (df["amount"] <= 0)]
    if not invalid.empty:
        raise ValueError(f"scholarship amount must be positive and finite; bad rows: {list(invalid.index)}")

    df = df.set_index("scholarship_id")

    if not df.index.is_unique:
        dupes = list(df.index[df.index.duplicated()])
        raise ValueError(f"Duplicate scholarship_id values: {dupes}")

    warnings = []
    crit_cols = [c for c in df.columns if c.startswith("crit__")]
    unrecognized = [c for c in crit_cols if not CRIT_PATTERN.match(c)]
    if unrecognized:
        warnings.append(f"Unrecognized criterion column names (will be ignored): {unrecognized}")

    valid_crit_cols = [c for c in crit_cols if CRIT_PATTERN.match(c)]

    criteria: dict[str, list[Criterion]] = {}
    for sid in df.index:
        row = df.loc[sid]
        active = []
        for col in valid_crit_cols:
            cell = str(row[col]).strip().lower()
            if cell == "true":
                m = CRIT_PATTERN.match(col)
                active.append(Criterion(
                    attribute=m.group(1),
                    operator=m.group(2),
                    value=m.group(3),
                    column=col,
                ))
        criteria[sid] = active

    return df, criteria, warnings


def validate_balance(recipients: pd.DataFrame, scholarships: pd.DataFrame) -> dict:
    """Check that total award amounts equal total scholarship pool."""
    total_awards = recipients["award_amount"].sum()
    total_pool = scholarships["amount"].sum()
    delta = total_awards - total_pool
    return {
        "balanced": bool(abs(delta) < 0.01),
        "total_awards": float(total_awards),
        "total_pool": float(total_pool),
        "delta": float(delta),
    }


def load_all(recipients_source, scholarships_source) -> LoadResult:
    """Convenience: load both files and return a LoadResult."""
    recipients = load_recipients(recipients_source)
    scholarships, criteria, warnings = load_scholarships(scholarships_source)
    return LoadResult(
        recipients=recipients,
        scholarships=scholarships,
        scholarship_criteria=criteria,
        warnings=warnings,
    )


def _read_csv(source: str | bytes | io.IOBase) -> pd.DataFrame:
    # dtype=str loads all columns as strings, bypassing pandas type inference.
    # This prevents silent coercions (e.g. "3.0" -> 3, "TRUE" -> True) that would
    # cause mismatches against the string values in criterion definitions.
    # Numeric columns (award_amount, amount) are explicitly coerced after load.
    if isinstance(source, bytes):
        source = io.BytesIO(source)
    return pd.read_csv(source, dtype=str)
