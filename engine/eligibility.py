"""Boolean eligibility matrix: recipients × scholarships."""

from __future__ import annotations

import pandas as pd

from engine.loader import Criterion


def _evaluate_criterion_vectorized(recipients: pd.DataFrame, crit: Criterion) -> pd.Series:
    """Return a boolean Series over all recipients for a single criterion."""
    if crit.attribute not in recipients.columns:
        return pd.Series(False, index=recipients.index)
    col = recipients[crit.attribute]
    if crit.operator == "eq":
        return col == crit.value
    if crit.operator == "gte":
        return pd.to_numeric(col, errors="coerce") >= float(crit.value)
    if crit.operator == "lte":
        return pd.to_numeric(col, errors="coerce") <= float(crit.value)
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
