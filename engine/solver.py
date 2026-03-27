"""LP-based scholarship assignment solver using PuLP/CBC."""

from __future__ import annotations

import time
from dataclasses import dataclass, field

import pandas as pd
import pulp


@dataclass
class SolveResult:
    status: str                          # "Optimal", "Infeasible", "Timeout", "Error"
    allocations: pd.DataFrame            # columns: recipient_id, scholarship_id, amount
    infeasible_recipients: list[str]     # recipient_ids removed before solve (insufficient eligible capacity)
    solve_time_s: float
    message: str = ""


def solve(
    recipients: pd.DataFrame,
    scholarships: pd.DataFrame,
    eligibility: pd.DataFrame,
    min_split_amount: float = 0.0,
    timeout_seconds: int = 120,
) -> SolveResult:
    """
    Assign scholarship funds to recipients via linear programming.

    recipients: DataFrame indexed by recipient_id, must have 'award_amount' column
    scholarships: DataFrame indexed by scholarship_id, must have 'amount' column
    eligibility: bool DataFrame, index=recipient_id, columns=scholarship_id
    """
    t0 = time.monotonic()

    # --- Pre-solve infeasibility check ---
    infeasible = []
    eligible_capacity = {}
    for rid in recipients.index:
        cap = scholarships.loc[eligibility.loc[rid][eligibility.loc[rid]].index, "amount"].sum()
        eligible_capacity[rid] = float(cap)

    for rid in recipients.index:
        if eligible_capacity[rid] < recipients.loc[rid, "award_amount"] - 0.01:
            infeasible.append(rid)

    solvable = [r for r in recipients.index if r not in infeasible]
    if not solvable:
        return SolveResult(
            status="Infeasible",
            allocations=_empty_allocations(),
            infeasible_recipients=infeasible,
            solve_time_s=time.monotonic() - t0,
            message="No recipients could be funded given current scholarship criteria.",
        )

    recip_sub = recipients.loc[solvable]

    # --- Build LP ---
    prob = pulp.LpProblem("scholarship_assignment", pulp.LpMinimize)

    # Compute per-scholarship weights: tighter scholarships get higher weight
    # so the solver prefers filling them first
    eligible_counts = eligibility.loc[solvable].sum(axis=0).replace(0, 1)  # avoid div/0
    weights = {sid: 1.0 / float(eligible_counts[sid]) for sid in scholarships.index}

    # Decision variables: x[rid, sid] = dollars from scholarship sid to recipient rid
    # Only create variables for eligible pairs
    x = {}
    for rid in solvable:
        for sid in scholarships.index:
            if eligibility.loc[rid, sid]:
                x[rid, sid] = pulp.LpVariable(f"x_{rid}_{sid}", lowBound=0)

    if not x:
        return SolveResult(
            status="Infeasible",
            allocations=_empty_allocations(),
            infeasible_recipients=infeasible,
            solve_time_s=time.monotonic() - t0,
            message="No eligible (recipient, scholarship) pairs found.",
        )

    # Objective: minimize weighted sum (prefer tight scholarships)
    prob += pulp.lpSum(weights[sid] * x[rid, sid] for (rid, sid) in x)

    # Constraint: each recipient must be fully funded
    for rid in solvable:
        eligible_sids = [sid for sid in scholarships.index if (rid, sid) in x]
        prob += (
            pulp.lpSum(x[rid, sid] for sid in eligible_sids) == recip_sub.loc[rid, "award_amount"],
            f"fund_{rid}",
        )

    # Constraint: each scholarship cannot be over-allocated
    for sid in scholarships.index:
        eligible_rids = [rid for rid in solvable if (rid, sid) in x]
        if eligible_rids:
            prob += (
                pulp.lpSum(x[rid, sid] for rid in eligible_rids) <= scholarships.loc[sid, "amount"],
                f"cap_{sid}",
            )

    # --- Solve ---
    solver = pulp.PULP_CBC_CMD(timeLimit=timeout_seconds, msg=0)
    prob.solve(solver)

    elapsed = time.monotonic() - t0
    status_str = pulp.LpStatus[prob.status]

    if prob.status == pulp.constants.LpStatusInfeasible:
        return SolveResult(
            status="Infeasible",
            allocations=_empty_allocations(),
            infeasible_recipients=infeasible,
            solve_time_s=elapsed,
            message="LP is infeasible. Check scholarship capacity vs. recipient award totals.",
        )

    if prob.status not in (pulp.constants.LpStatusOptimal,):
        return SolveResult(
            status=status_str,
            allocations=_empty_allocations(),
            infeasible_recipients=infeasible,
            solve_time_s=elapsed,
            message=f"Solver returned status: {status_str}",
        )

    # --- Extract results ---
    rows = []
    for (rid, sid), var in x.items():
        val = pulp.value(var)
        if val is not None and val > 1e-6:
            rows.append({"recipient_id": rid, "scholarship_id": sid, "amount": round(val, 2)})

    allocations = pd.DataFrame(rows, columns=["recipient_id", "scholarship_id", "amount"])

    return SolveResult(
        status="Optimal",
        allocations=allocations,
        infeasible_recipients=infeasible,
        solve_time_s=elapsed,
    )


def _empty_allocations() -> pd.DataFrame:
    return pd.DataFrame(columns=["recipient_id", "scholarship_id", "amount"])
