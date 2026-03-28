"""Boolean eligibility matrix: recipients × scholarships.

Design note: all criteria for a scholarship are AND'd together — a recipient must satisfy
every active criterion to be eligible. OR logic is not supported in MVP. If a scholarship
has no active criteria, it is universally eligible (open to all recipients).
"""

from __future__ import annotations

import pandas as pd

from engine.loader import Criterion


def _evaluate_criterion_vectorized(recipients: pd.DataFrame, crit: Criterion) -> pd.Series:
    """Evaluate a single criterion against all recipients at once.

    Returns a boolean Series (index=recipient_id) where True means the recipient
    satisfies this criterion. Operates on the entire column at once rather than
    looping per recipient — each pandas operation here runs across all ~200 rows
    simultaneously in C, not Python.
    """
    if crit.attribute not in recipients.columns:
        raise ValueError(
            f"Criterion references attribute '{crit.attribute}' which is not a column in the "
            f"recipients CSV (column: '{crit.column}'). Check for typos in the scholarship criteria."
        )
    col = recipients[crit.attribute]
    if crit.operator == "eq":
        return col == crit.value
    if crit.operator in ("gte", "lte"):
        numeric = pd.to_numeric(col, errors="coerce")
        bad = col[numeric.isna()]
        if not bad.empty:
            raise ValueError(
                f"Cannot apply '{crit.operator}' criterion on '{crit.attribute}': "
                f"non-numeric values found: {bad.unique().tolist()}"
            )
        if crit.operator == "gte":
            return numeric >= float(crit.value)
        return numeric <= float(crit.value)
    if crit.operator == "contains":
        return col.str.contains(crit.value, na=False)
    return pd.Series(False, index=recipients.index)


def build_matrix(
    recipients: pd.DataFrame,
    scholarships: pd.DataFrame,
    criteria: dict[str, list[Criterion]],
) -> pd.DataFrame:
    """Build boolean eligibility matrix.

    Returns DataFrame with recipient_id as index, scholarship_id as columns.
    True = recipient is eligible for that scholarship.
    """
    matrix = pd.DataFrame(False, index=recipients.index, columns=scholarships.index)

    for sid in scholarships.index:
        crit_list = criteria.get(sid, [])
        if not crit_list:
            matrix[sid] = True
            continue

        # AND-accumulator pattern: start with everyone eligible (all True),
        # then narrow the set by ANDing in each criterion's boolean mask.
        # After all criteria, eligible[rid] is True only if the recipient
        # passed every criterion. The &= operator is element-wise boolean AND
        # across the full Series — not a scalar operation.
        eligible = pd.Series(True, index=recipients.index)
        for crit in crit_list:
            eligible &= _evaluate_criterion_vectorized(recipients, crit)
        matrix[sid] = eligible

    return matrix


def summarize_coverage(matrix: pd.DataFrame) -> dict:
    """Return coverage stats for UI display."""
    recipients_per_scholarship = matrix.sum(axis=0)
    scholarships_per_recipient = matrix.sum(axis=1)

    zero_eligibility = (scholarships_per_recipient == 0)

    return {
        "recipients_per_scholarship": recipients_per_scholarship.to_dict(),
        "scholarships_per_recipient": scholarships_per_recipient.to_dict(),
        "recipients_with_zero_eligibility": list(zero_eligibility[zero_eligibility].index),
        "min_scholarships_per_recipient": int(scholarships_per_recipient.min()),
        "max_scholarships_per_recipient": int(scholarships_per_recipient.max()),
    }
