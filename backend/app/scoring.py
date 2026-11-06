import re

def score_candidate(candidate, job) -> dict:
    # Deliberately excludes name, email, phone, gender, age, photo and marital status.
    text = (candidate.resume_text or "").lower()
    candidate_skills = {s.lower() for s in (candidate.skills or [])}
    required = [s.strip() for s in (job.required_skills or []) if s.strip()]
    evidence = []
    skill_points = 0
    if required:
        per = 40 / len(required)
        for skill in required:
            found = skill.lower() in candidate_skills or skill.lower() in text
            if found:
                skill_points += per
                match = re.search(re.escape(skill), candidate.resume_text or "", re.I)
                excerpt = (candidate.resume_text[max(0, match.start()-55):match.end()+100].replace("\n", " ")
                           if match else f"Parsed skill: {skill}")
                evidence.append({"criterion": f"Skill: {skill}", "status": "matched", "excerpt": excerpt[:220]})
            else:
                evidence.append({"criterion": f"Skill: {skill}", "status": "not_found", "excerpt": "No supporting text found in the extracted resume."})

    exp = candidate.experience_years or 0
    if job.min_experience <= exp <= job.max_experience:
        exp_points = 30
        exp_status = "matched"
        exp_excerpt = f"Parsed experience: {exp:g} years"
    elif exp == 0:
        exp_points = 8
        exp_status = "unknown"
        exp_excerpt = "Experience could not be reliably extracted; recruiter review required."
    else:
        exp_points = max(0, 30 - abs(exp - job.min_experience) * 8)
        exp_status = "partial"
        exp_excerpt = f"Parsed experience: {exp:g} years; target: {job.min_experience:g}-{job.max_experience:g} years"
    evidence.append({"criterion": "Experience", "status": exp_status, "excerpt": exp_excerpt})

    notice = candidate.notice_days
    if notice is None:
        notice_points, notice_status, notice_excerpt = 10, "unknown", "Notice period not found in extracted resume."
    elif notice <= job.max_notice_days:
        notice_points, notice_status, notice_excerpt = 20, "matched", f"Parsed notice period: {notice} days"
    else:
        notice_points, notice_status, notice_excerpt = max(0, 20 - (notice-job.max_notice_days)*0.4), "partial", f"Parsed notice period: {notice} days; maximum: {job.max_notice_days}"
    evidence.append({"criterion": "Notice period", "status": notice_status, "excerpt": notice_excerpt})

    loc = (candidate.location or "").lower()
    target = (job.location or "").lower()
    location_points = 10 if target and target in loc else 5
    evidence.append({"criterion": "Location", "status": "matched" if location_points == 10 else "unknown", "excerpt": f"Candidate location: {candidate.location}; job location: {job.location}"})

    score = round(min(100, skill_points + exp_points + notice_points + location_points), 1)
    return {
        "score": score,
        "engine": "rules_fallback",
        "evidence": evidence,
        "explanation": "Advisory match score based on job criteria and extracted resume evidence. A recruiter must review the original CV; no automatic rejection occurs."
    }
