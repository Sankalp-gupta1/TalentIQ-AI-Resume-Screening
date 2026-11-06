import re
from pathlib import Path
import fitz
from docx import Document

def extract_text(path: str) -> str:
    suffix = Path(path).suffix.lower()
    if suffix == ".pdf":
        with fitz.open(path) as pdf:
            return "\n".join(page.get_text("text") for page in pdf)
    if suffix == ".docx":
        doc = Document(path)
        return "\n".join(p.text for p in doc.paragraphs)
    raise ValueError("Only PDF and DOCX files are supported")

def parse_profile(text: str) -> dict:
    clean = re.sub(r"[ \t]+", " ", text)
    exp_match = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", clean, re.I)
    notice_match = re.search(r"(?:notice(?:\s+period)?\s*[:\-]?\s*(\d+)\s*days?|(?<!\d)(\d+)\s*days?\s*(?:notice(?:\s+period)?)?)", clean, re.I)
    email_match = re.search(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", clean, re.I)
    phone_match = re.search(r"(?<!\d)(?:\+91[- ]?)?[6-9]\d{9}(?!\d)", clean)
    known = ["python", "java", "spring boot", "microservices", "sql", "react", "node.js",
             "fastapi", "django", "machine learning", "tensorflow", "pytorch", "aws",
             "hibernate", "rest api", "excel", "aml", "kyc", "docker", "kubernetes"]
    low = clean.lower()
    skills = [s for s in known if s in low]
    lines = [x.strip() for x in clean.splitlines() if x.strip()]
    name = lines[0][:150] if lines else "Candidate (name needs review)"
    return {
        "name": name,
        "experience_years": float(exp_match.group(1)) if exp_match else 0,
        "notice_days": int(next(g for g in notice_match.groups() if g)) if notice_match else None,
        "skills": skills,
        "email": email_match.group(0) if email_match else None,
        "phone": phone_match.group(0) if phone_match else None,
        "current_role": lines[1][:150] if len(lines) > 1 else "Not specified",
        "location": "Not specified",
    }
