from types import SimpleNamespace
from app.scoring import score_candidate

def test_scoring_uses_job_evidence_and_never_name():
    candidate=SimpleNamespace(name="Secret Name",skills=["Java","Spring Boot","Microservices"],
        experience_years=6.5,notice_days=60,location="Noida",
        resume_text="Java Spring Boot microservices engineer with 6.5 years experience. Notice period 60 days.")
    job=SimpleNamespace(required_skills=["Java","Spring Boot","Microservices"],min_experience=5,
        max_experience=8,max_notice_days=60,location="Noida")
    result=score_candidate(candidate,job)
    assert result["score"] == 100
    assert result["engine"] == "rules_fallback"
    assert all("Secret Name" not in e["excerpt"] for e in result["evidence"])

def test_missing_notice_is_unknown_not_automatic_reject():
    candidate=SimpleNamespace(name="Candidate",skills=["Java"],experience_years=5,notice_days=None,
        location="Noida",resume_text="Java engineer, 5 years.")
    job=SimpleNamespace(required_skills=["Java"],min_experience=5,max_experience=8,
        max_notice_days=60,location="Noida")
    result=score_candidate(candidate,job)
    assert any(e["status"]=="unknown" for e in result["evidence"])
    assert result["score"] > 0
