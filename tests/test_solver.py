"""Solver tests using known-answer cases."""

import pandas as pd
import pytest
from engine.loader import load_recipients, load_scholarships
from engine.eligibility import build_matrix
from engine.solver import solve


# --- Minimal known-answer fixture ---
# 3 recipients, 3 scholarships, hand-verifiable solution
#
# R001 (nursing, first_gen): eligible S001(nursing,$3000), S003(general,$1000)  award=$2000
# R002 (engineering):        eligible S002(stem,$2000), S003(general,$1000)     award=$2000
# R003 (nursing, first_gen): eligible S001(nursing,$3000), S003(general,$1000)  award=$2000
# Total awards = $6000, total pool = $6000
#
# S001 must split between R001 and R003 (only nursing-eligible).
# S002 goes entirely to R002.
# S003 fills gaps.

RECIP_CSV = b"""recipient_id,full_name,award_amount,major,stem_flag,first_gen
R001,Alice,2000,nursing,false,true
R002,Bob,2000,engineering,true,false
R003,Carol,2000,nursing,false,true
"""

SCHOL_CSV = b"""scholarship_id,name,amount,crit__major__eq__nursing,crit__stem_flag__eq__true
S001,Nursing Award,3000,true,false
S002,STEM Award,2000,false,true
S003,General Award,1000,false,false
"""


def _setup():
    recip = load_recipients(RECIP_CSV)
    schol, crit, _ = load_scholarships(SCHOL_CSV)
    matrix = build_matrix(recip, schol, crit)
    return recip, schol, matrix


def test_solve_optimal_status():
    recip, schol, matrix = _setup()
    result = solve(recip, schol, matrix)
    assert result.status == "Optimal"


def test_solve_no_infeasible_recipients():
    recip, schol, matrix = _setup()
    result = solve(recip, schol, matrix)
    assert result.infeasible_recipients == []


def test_solve_recipients_fully_funded():
    """Every solvable recipient's total allocation equals their award amount."""
    recip, schol, matrix = _setup()
    result = solve(recip, schol, matrix)
    totals = result.allocations.groupby("recipient_id")["amount"].sum()
    for rid in recip.index:
        assert totals[rid] == pytest.approx(recip.loc[rid, "award_amount"], abs=0.02)


def test_solve_scholarships_not_overallocated():
    """No scholarship disbursed more than its total amount."""
    recip, schol, matrix = _setup()
    result = solve(recip, schol, matrix)
    disbursed = result.allocations.groupby("scholarship_id")["amount"].sum()
    for sid in disbursed.index:
        assert disbursed[sid] <= schol.loc[sid, "amount"] + 0.02


def test_solve_eligibility_respected():
    """No allocation from a scholarship to an ineligible recipient."""
    recip, schol, matrix = _setup()
    result = solve(recip, schol, matrix)
    for _, row in result.allocations.iterrows():
        assert matrix.loc[row["recipient_id"], row["scholarship_id"]], (
            f"{row['recipient_id']} incorrectly assigned to {row['scholarship_id']}"
        )


def test_solve_stem_award_goes_to_bob():
    """R002 (only STEM-eligible recipient) should receive all of S002."""
    recip, schol, matrix = _setup()
    result = solve(recip, schol, matrix)
    r002_s002 = result.allocations[
        (result.allocations["recipient_id"] == "R002") &
        (result.allocations["scholarship_id"] == "S002")
    ]["amount"].sum()
    # R002 is the only eligible recipient for S002, so R002 should get all $2000 from S002
    assert r002_s002 == pytest.approx(2000.0, abs=0.02)


def test_solve_infeasible_recipient_flagged():
    """Recipient with insufficient eligible scholarship capacity is flagged, not solved."""
    # R999 only qualifies for a $500 scholarship but needs $2000
    recip = load_recipients(b"recipient_id,full_name,award_amount,major\nR999,Zoe,2000,art\n")
    schol, crit, _ = load_scholarships(
        b"scholarship_id,name,amount,crit__major__eq__art\nS001,Art Award,500,true\n"
    )
    matrix = build_matrix(recip, schol, crit)
    result = solve(recip, schol, matrix)
    assert "R999" in result.infeasible_recipients


def test_solve_all_infeasible_returns_infeasible_status():
    recip = load_recipients(b"recipient_id,full_name,award_amount,major\nR999,Zoe,2000,art\n")
    schol, crit, _ = load_scholarships(
        b"scholarship_id,name,amount,crit__major__eq__nursing\nS001,Nursing,500,true\n"
    )
    matrix = build_matrix(recip, schol, crit)
    result = solve(recip, schol, matrix)
    assert result.status == "Infeasible"
    assert "R999" in result.infeasible_recipients
