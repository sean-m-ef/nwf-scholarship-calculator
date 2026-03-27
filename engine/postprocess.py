"""Post-solve analysis: summaries, flags, gap detection."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from engine.solver import SolveResult


@dataclass
class ProcessedResult:
    solve_result: SolveResult
    allocations: pd.DataFrame          # enriched with recipient/scholarship names + small_split flag
    recipient_summary: pd.DataFrame    # per-recipient: awarded, allocated, gap, # scholarships, flags
    scholarship_summary: pd.DataFrame  # per-scholarship: available, disbursed, remaining, # recipients


def process(
    result: SolveResult,
    recipients: pd.DataFrame,
    scholarships: pd.DataFrame,
    min_split_amount: float = 100.0,
) -> ProcessedResult:
    """Enrich solve results with summaries and flags."""
    alloc = result.allocations.copy()

    if alloc.empty:
        return ProcessedResult(
            solve_result=result,
            allocations=alloc,
            recipient_summary=_empty_recipient_summary(recipients, result.infeasible_recipients),
            scholarship_summary=_empty_scholarship_summary(scholarships),
        )

    # --- Enrich allocations ---
    alloc = alloc.merge(
        recipients[["full_name"]].reset_index().rename(columns={"full_name": "recipient_name"}),
        on="recipient_id",
        how="left",
    )
    alloc = alloc.merge(
        scholarships[["name"]].reset_index().rename(columns={"name": "scholarship_name"}),
        on="scholarship_id",
        how="left",
    )
    alloc["small_split"] = alloc["amount"] < min_split_amount
    alloc = alloc[["recipient_id", "recipient_name", "scholarship_id", "scholarship_name", "amount", "small_split"]]

    # --- Recipient summary ---
    per_recip = alloc.groupby("recipient_id").agg(
        total_allocated=("amount", "sum"),
        num_scholarships=("scholarship_id", "count"),
        has_small_split=("small_split", "any"),
    ).reset_index()

    recip_info = recipients[["full_name", "award_amount"]].reset_index()
    recip_sum = recip_info.merge(per_recip, on="recipient_id", how="left")
    recip_sum["total_allocated"] = recip_sum["total_allocated"].fillna(0.0)
    recip_sum["num_scholarships"] = recip_sum["num_scholarships"].fillna(0).astype(int)
    recip_sum["has_small_split"] = recip_sum["has_small_split"].fillna(False)
    recip_sum["gap"] = recip_sum["award_amount"] - recip_sum["total_allocated"]
    recip_sum["infeasible"] = recip_sum["recipient_id"].isin(result.infeasible_recipients)
    recip_sum = recip_sum.rename(columns={"full_name": "name"})
    recip_sum = recip_sum[["recipient_id", "name", "award_amount", "total_allocated", "gap", "num_scholarships", "has_small_split", "infeasible"]]

    # --- Scholarship summary ---
    per_schol = alloc.groupby("scholarship_id").agg(
        total_disbursed=("amount", "sum"),
        num_recipients=("recipient_id", "count"),
    ).reset_index()

    schol_info = scholarships[["name", "amount"]].reset_index()
    schol_sum = schol_info.merge(per_schol, on="scholarship_id", how="left")
    schol_sum["total_disbursed"] = schol_sum["total_disbursed"].fillna(0.0)
    schol_sum["num_recipients"] = schol_sum["num_recipients"].fillna(0).astype(int)
    schol_sum["remaining"] = schol_sum["amount"] - schol_sum["total_disbursed"]
    schol_sum = schol_sum.rename(columns={"name": "scholarship_name", "amount": "total_available"})
    schol_sum = schol_sum[["scholarship_id", "scholarship_name", "total_available", "total_disbursed", "remaining", "num_recipients"]]

    return ProcessedResult(
        solve_result=result,
        allocations=alloc,
        recipient_summary=recip_sum,
        scholarship_summary=schol_sum,
    )


def _empty_recipient_summary(recipients: pd.DataFrame, infeasible: list[str]) -> pd.DataFrame:
    df = recipients[["full_name", "award_amount"]].reset_index().copy()
    df["total_allocated"] = 0.0
    df["gap"] = df["award_amount"]
    df["num_scholarships"] = 0
    df["has_small_split"] = False
    df["infeasible"] = df["recipient_id"].isin(infeasible)
    return df.rename(columns={"full_name": "name"})[
        ["recipient_id", "name", "award_amount", "total_allocated", "gap", "num_scholarships", "has_small_split", "infeasible"]
    ]


def _empty_scholarship_summary(scholarships: pd.DataFrame) -> pd.DataFrame:
    df = scholarships[["name", "amount"]].reset_index().copy()
    df["total_disbursed"] = 0.0
    df["remaining"] = df["amount"]
    df["num_recipients"] = 0
    return df.rename(columns={"name": "scholarship_name", "amount": "total_available"})[
        ["scholarship_id", "scholarship_name", "total_available", "total_disbursed", "remaining", "num_recipients"]
    ]
