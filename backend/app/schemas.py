from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class JobIn(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    company: str = "Company A"
    location: str = "Noida"
    description: str = ""
    min_experience: float = 0
    max_experience: float = 99
    required_skills: list[str] = []
    max_notice_days: int = 90
    ctc: str = "Not specified"

class ScorecardUpdate(BaseModel):
    min_experience: float
    max_experience: float
    required_skills: list[str]
    max_notice_days: int
    location: str
    ctc: str = "Not specified"

class ClientDecision(BaseModel):
    status: str
    reason: Optional[str] = None
    interview_slot: Optional[str] = None
