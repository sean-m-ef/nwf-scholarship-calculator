"""Boolean eligibility matrix: recipients × scholarships."""

from __future__ import annotations

import pandas as pd

from engine.loader import Criterion


def _evaluate_criterion(recipient_row: pd.Series, crit: Criterion) -> bool:
    """Return True if recipient satisfies the criterion."""
    attr = crit.attribute
    if attr not in recipient_row.index:
        return False  # unknown attribute = not eligible

    raw = str(recipient_row[attr]).strip().lower()
    val = crit.value.strip().lower()

    if crit.operator == "eq":
        return raw == val
    if crit.operator == "gte":
        try:
            return float(raw) >= float(val)
        except ValueError:
            return False
    if crit.operator == "lte":
        try:
            return float(raw) <= float(val)
        except ValueError:
            return False
    if crit.operator == "contains":
        return val in raw
    return False  # unknown operator = not eligible


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
            # No criteria = universally eligible
            matrix[sid] = True
            continue
        for rid in recipients.index:
            row = recipients.loc[rid]
            matrix.loc[rid, sid] = all(_evaluate_criterion(row, c) for c in crit_list)

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
