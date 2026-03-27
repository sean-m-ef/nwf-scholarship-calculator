import io
import pytest
import pandas as pd
from engine.loader import load_recipients, load_scholarships, validate_balance, load_all, Criterion

RECIPIENTS_CSV = """recipient_id,full_name,award_amount,major,gpa,first_gen
R001,Jane Smith,2500,nursing,3.8,true
R002,Maria Garcia,3000,engineering,3.6,false
"""

SCHOLARSHIPS_CSV = """scholarship_id,name,amount,crit__major__eq__nursing,crit__first_gen__eq__true
S001,Nursing Award,3000,true,false
S002,First Gen Award,2500,false,true
"""

SCHOLARSHIPS_UNRECOGNIZED_CSV = """scholarship_id,name,amount,crit__major__eq__nursing,crit__badcolumn
S001,Nursing Award,5500,true,true
"""


def _bytes(s):
    return s.strip().encode()


def test_load_recipients_basic():
    df = load_recipients(_bytes(RECIPIENTS_CSV))
    assert list(df.index) == ["R001", "R002"]
    assert df.loc["R001", "award_amount"] == 2500.0
    assert df.loc["R001", "major"] == "nursing"


def test_load_recipients_missing_column():
    bad = "recipient_id,full_name\nR001,Jane\n"
    with pytest.raises(ValueError, match="award_amount"):
        load_recipients(bad.encode())


def test_load_scholarships_parses_criteria():
    df, criteria, warnings = load_scholarships(_bytes(SCHOLARSHIPS_CSV))
    assert "S001" in criteria
    assert len(criteria["S001"]) == 1
    c = criteria["S001"][0]
    assert c.attribute == "major"
    assert c.operator == "eq"
    assert c.value == "nursing"

    assert len(criteria["S002"]) == 1
    assert criteria["S002"][0].attribute == "first_gen"


def test_load_scholarships_no_criteria():
    csv = "scholarship_id,name,amount\nS001,General,5000\n"
    df, criteria, warnings = load_scholarships(csv.encode())
    assert criteria["S001"] == []


def test_load_scholarships_unrecognized_column_warns():
    _, _, warnings = load_scholarships(_bytes(SCHOLARSHIPS_UNRECOGNIZED_CSV))
    assert any("crit__badcolumn" in w for w in warnings)


def test_validate_balance_balanced():
    recip = load_recipients(_bytes(RECIPIENTS_CSV))
    schol, _, _ = load_scholarships(_bytes(SCHOLARSHIPS_CSV))
    result = validate_balance(recip, schol)
    assert result["balanced"] is True
    assert result["delta"] == pytest.approx(0.0)


def test_validate_balance_unbalanced():
    recip = load_recipients(_bytes(RECIPIENTS_CSV))
    unbalanced_csv = """scholarship_id,name,amount
S001,General,4000
"""
    schol, _, _ = load_scholarships(unbalanced_csv.encode())
    result = validate_balance(recip, schol)
    assert result["balanced"] is False
    assert result["delta"] == pytest.approx(1500.0)


def test_full_name_case_preserved():
    csv = b"recipient_id,full_name,award_amount,major\nR001,Jane Smith,1000,nursing\n"
    df = load_recipients(csv)
    assert df.loc["R001", "full_name"] == "Jane Smith"
    assert df.loc["R001", "major"] == "nursing"  # attribute columns still lowercased


def test_negative_award_amount_rejected():
    csv = b"recipient_id,full_name,award_amount\nR001,Jane,-500\n"
    with pytest.raises(ValueError, match="positive"):
        load_recipients(csv)


def test_negative_scholarship_amount_rejected():
    csv = b"scholarship_id,name,amount\nS001,Award,-1000\n"
    with pytest.raises(ValueError, match="positive"):
        load_scholarships(csv)


def test_duplicate_recipient_id_rejected():
    csv = b"recipient_id,full_name,award_amount\nR001,Jane,1000\nR001,Jane Dupe,1000\n"
    with pytest.raises(ValueError, match="Duplicate recipient_id"):
        load_recipients(csv)


def test_duplicate_scholarship_id_rejected():
    csv = b"scholarship_id,name,amount\nS001,Award,1000\nS001,Award Dupe,1000\n"
    with pytest.raises(ValueError, match="Duplicate scholarship_id"):
        load_scholarships(csv)
