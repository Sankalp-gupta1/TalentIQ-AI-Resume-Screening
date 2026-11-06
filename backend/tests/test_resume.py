from app.resume import parse_profile

def test_profile_extracts_common_fields():
    p=parse_profile("Alex Doe\nPython Developer\n4 years experience with Python and FastAPI. Notice period 30 days.\nalex@example.com")
    assert p["experience_years"] == 4
    assert p["notice_days"] == 30
    assert "python" in p["skills"]
    assert p["email"] == "alex@example.com"

def test_profile_extracts_notice_when_notice_precedes_days():
    p=parse_profile("Sam Candidate\nBackend Engineer\n5 years experience. Notice period: 45 days.")
    assert p["notice_days"] == 45


def test_profile_extracts_days_notice_variant():
    p=parse_profile("Sam Candidate\nBackend Engineer\n5 years experience. 30 days notice.")
    assert p["notice_days"] == 30
