import pandas as pd
import pytest
from engine.loader import Criterion, load_recipients, load_scholarships
from engine.eligibility import build_matrix, summarize_coverage

RECIPIENTS_CSV = b"""recipient_id,full_name,award_amount,major,gpa,first_gen,stem_flag
R001,Jane,2500,nursing,3.8,true,false
R002,Maria,2000,engineering,3.6,false,true
R003,Aisha,1500,education,3.2,true,false
"""

SCHOLARSHIPS_CSV = b"""scholarship_id,name,amount,crit__major__eq__nursing,crit__gpa__gte__3.5,crit__first_gen__eq__true,crit__stem_flag__eq__true
S001,Nursing Award,3000,true,false,false,false
S002,High GPA Award,2000,false,true,false,false
S003,First Gen Award,1500,false,false,true,false
S004,General Award,1000,false,false,false,false
"""


def load():
    recip = load_recipients(RECIPIENTS_CSV)
    schol, crit, _ = load_scholarships(SCHOLARSHIPS_CSV)
    return recip, schol, crit


def test_nursing_award_only_nurses():
    recip, schol, crit = load()
    matrix = build_matrix(recip, schol, crit)
    assert matrix.loc["R001", "S001"] == True   # nursing
    assert matrix.loc["R002", "S001"] == False  # engineering
    assert matrix.loc["R003", "S001"] == False  # education


def test_gpa_gte_operator():
    recip, schol, crit = load()
    matrix = build_matrix(recip, schol, crit)
    assert matrix.loc["R001", "S002"] == True   # gpa 3.8 >= 3.5
    assert matrix.loc["R002", "S002"] == True   # gpa 3.6 >= 3.5
    assert matrix.loc["R003", "S002"] == False  # gpa 3.2 < 3.5


def test_universal_scholarship():
    recip, schol, crit = load()
    matrix = build_matrix(recip, schol, crit)
    # S004 has no criteria — everyone eligible
    assert matrix["S004"].all()


def test_first_gen_boolean():
    recip, schol, crit = load()
    matrix = build_matrix(recip, schol, crit)
    assert matrix.loc["R001", "S003"] == True   # first_gen=true
    assert matrix.loc["R002", "S003"] == False  # first_gen=false
    assert matrix.loc["R003", "S003"] == True


def test_unknown_attribute_ineligible():
    """Criterion referencing an attribute not in recipients CSV -> ineligible."""
    recip = load_recipients(b"recipient_id,full_name,award_amount\nR001,Jane,1000\n")
    schol, crit, _ = load_scholarships(b"scholarship_id,name,amount,crit__major__eq__nursing\nS001,Award,1000,true\n")
    matrix = build_matrix(recip, schol, crit)
    assert matrix.loc["R001", "S001"] == False


def test_summarize_coverage():
    recip, schol, crit = load()
    matrix = build_matrix(recip, schol, crit)
    summary = summarize_coverage(matrix)
    # R001 eligible for S001, S002, S003, S004 = 4
    assert summary["scholarships_per_recipient"]["R001"] == 4
    # R002 eligible for S002, S004 = 2
    assert summary["scholarships_per_recipient"]["R002"] == 2
    assert summary["recipients_with_zero_eligibility"] == []


def test_zero_eligibility_detection():
    """Recipient with no matching scholarships is flagged."""
    recip = load_recipients(b"recipient_id,full_name,award_amount,major\nR001,Jane,1000,art\n")
    schol, crit, _ = load_scholarships(b"scholarship_id,name,amount,crit__major__eq__nursing\nS001,Award,1000,true\n")
    matrix = build_matrix(recip, schol, crit)
    summary = summarize_coverage(matrix)
    assert "R001" in summary["recipients_with_zero_eligibility"]
