import os, uuid, hashlib
from pathlib import Path
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import Base, engine, get_db
from app.models import User, Job, Candidate, Score, Submission, PipelineEvent, AuditLog
from app.auth import verify_password, create_token, current_user, require_role
from app.schemas import JobIn, ScorecardUpdate, ClientDecision, LoginIn
from app.resume import extract_text, parse_profile
from app.scoring import score_candidate
from app.ai import extract_job_with_ai
from app.config import settings

Base.metadata.create_all(bind=engine)
app = FastAPI(title="TalentIQ API", description="AI-powered Recruitment Management Platform", version="1.0.0")
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def log(db, user, action, resource_type, resource_id):
    db.add(AuditLog(user_id=user.id, action=action, resource_type=resource_type, resource_id=str(resource_id)))
    db.commit()

def candidate_access(db, user, candidate_id):
    c = db.get(Candidate, candidate_id)
    if not c or c.deleted:
        raise HTTPException(404, "Candidate not found")
    if user.role == "client":
        sub = db.query(Submission).filter_by(candidate_id=c.id, client_id=user.client_id).first()
        if not sub:
            raise HTTPException(403, "Candidate has not been shared with your organization")
    log(db, user, "view_candidate", "candidate", c.id)
    return c

@app.get("/")
def root():
    return {"success": True, "message": "Welcome to TalentIQ API", "docs": "/docs"}

@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "service": "TalentIQ API"}

@app.post("/api/v1/auth/login")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")
    return {"access_token": create_token(user), "token_type": "bearer",
            "user": {"id": user.id, "name": user.name, "email": user.email, "role": user.role}}

@app.get("/api/v1/auth/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role, "client_id": user.client_id}

@app.get("/api/v1/dashboard")
def dashboard(db: Session = Depends(get_db), user: User = Depends(current_user)):
    if user.role == "client":
        submissions = db.query(Submission).filter_by(client_id=user.client_id).all()
        return {"jobs": len({s.job_id for s in submissions}), "candidates": len(submissions),
                "pending": sum(s.status == "submitted" for s in submissions), "joined": sum(s.status == "joined" for s in submissions)}
    return {"jobs": db.query(Job).count(), "candidates": db.query(Candidate).filter_by(deleted=False).count(),
            "pending": db.query(Candidate).filter_by(deleted=False).count(), "joined": db.query(PipelineEvent).filter_by(status="joined").count()}

@app.get("/api/v1/jobs")
def list_jobs(db: Session = Depends(get_db), user: User = Depends(current_user)):
    jobs = db.query(Job).order_by(desc(Job.created_at)).all()
    if user.role == "client":
        allowed = {s.job_id for s in db.query(Submission).filter_by(client_id=user.client_id).all()}
        jobs = [j for j in jobs if j.id in allowed]
    return [{"id":j.id,"title":j.title,"company":j.company,"location":j.location,"status":j.status,
             "min_experience":j.min_experience,"max_experience":j.max_experience,
             "required_skills":j.required_skills,"max_notice_days":j.max_notice_days,"ctc":j.ctc} for j in jobs]

@app.post("/api/v1/jobs")
async def create_job(payload: JobIn, db: Session = Depends(get_db), user: User = Depends(require_role("recruiter"))):
    data = payload.model_dump()
    if payload.description:
        ai_data = await extract_job_with_ai(payload.description)
        if ai_data:
            for key in ["title","min_experience","max_experience","required_skills","max_notice_days","location","ctc"]:
                if key in ai_data and ai_data[key] is not None:
                    data[key] = ai_data[key]
    job = Job(**data, created_by=user.id)
    db.add(job); db.commit(); db.refresh(job)
    return {"id":job.id,"title":job.title,"scorecard":{"min_experience":job.min_experience,"max_experience":job.max_experience,
            "required_skills":job.required_skills,"max_notice_days":job.max_notice_days,"location":job.location,"ctc":job.ctc},
            "ai_extraction":"llm" if settings.openai_api_key else "manual_or_defaults"}

@app.patch("/api/v1/jobs/{job_id}/scorecard")
def update_scorecard(job_id: int, payload: ScorecardUpdate, db: Session = Depends(get_db), user: User = Depends(require_role("recruiter"))):
    job = db.get(Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    for k,v in payload.model_dump().items(): setattr(job,k,v)
    db.commit()
    return {"success":True,"message":"Scorecard updated"}

@app.post("/api/v1/jobs/{job_id}/resumes")
async def upload_resumes(job_id: int, files: list[UploadFile] = File(...), consent_confirmed: bool = Form(False), db: Session = Depends(get_db), user: User = Depends(require_role("recruiter"))):
    job = db.get(Job, job_id)
    if not job: raise HTTPException(404, "Job not found")
    if len(files) > settings.max_upload_files: raise HTTPException(400, f"Maximum {settings.max_upload_files} files per batch")
    if not consent_confirmed: raise HTTPException(400, "Confirm that candidates have consented to processing for this hiring purpose before uploading")
    results = []
    for file in files:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in [".pdf",".docx"]:
            results.append({"filename":file.filename,"status":"rejected","reason":"Only PDF and DOCX are supported"}); continue
        content = await file.read()
        if len(content) > 12 * 1024 * 1024:
            results.append({"filename":file.filename,"status":"rejected","reason":"File exceeds 12 MB"}); continue
        digest = hashlib.sha256(content).hexdigest()
        duplicate = db.query(Candidate).filter(Candidate.resume_path == f"sha256:{digest}", Candidate.job_id == job_id).first()
        if duplicate:
            results.append({"filename":file.filename,"status":"duplicate","candidate_id":duplicate.id}); continue
        safe_name = f"{uuid.uuid4().hex}{suffix}"
        path = UPLOAD_DIR / safe_name
        path.write_bytes(content)
        try:
            text = extract_text(str(path))
            if not text.strip():
                results.append({"filename":file.filename,"status":"needs_ocr","reason":"No selectable text found. OCR is not enabled in this MVP."})
                path.unlink(missing_ok=True); continue
            profile = parse_profile(text)
            c = Candidate(candidate_code=f"CND-{uuid.uuid4().hex[:8].upper()}", name=profile["name"],
                current_role=profile["current_role"], experience_years=profile["experience_years"], skills=profile["skills"],
                notice_days=profile["notice_days"], location=profile["location"], email=profile["email"], phone=profile["phone"],
                resume_path=f"sha256:{digest}", resume_text=text[:100000], job_id=job_id, consent_given=True, consent_at=datetime.now(timezone.utc))
            db.add(c); db.commit(); db.refresh(c)
            result = score_candidate(c,job)
            db.add(Score(candidate_id=c.id,job_id=job.id,**result))
            db.add(PipelineEvent(candidate_id=c.id,job_id=job.id,status="screened",note="Resume parsed and scored"))
            db.commit()
            results.append({"filename":file.filename,"status":"processed","candidate_id":c.id,"score":result["score"]})
        except Exception as e:
            db.rollback()
            path.unlink(missing_ok=True)
            results.append({"filename":file.filename,"status":"error","reason":str(e)[:180]})
    return {"total":len(files),"results":results}

@app.get("/api/v1/jobs/{job_id}/candidates")
def ranked_candidates(job_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("recruiter"))):
    rows = db.query(Candidate).filter_by(job_id=job_id,deleted=False).all()
    out = []
    for c in rows:
        s = db.query(Score).filter_by(candidate_id=c.id,job_id=job_id).order_by(desc(Score.created_at)).first()
        out.append({"id":c.id,"candidate_code":c.candidate_code,"name":c.name,"current_role":c.current_role,
                    "experience_years":c.experience_years,"skills":c.skills,"notice_days":c.notice_days,
                    "score":s.score if s else 0,"engine":s.engine if s else "not_scored","evidence":s.evidence if s else [],
                    "explanation":s.explanation if s else "Review required"})
    return sorted(out,key=lambda x:x["score"],reverse=True)

@app.get("/api/v1/candidates/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = candidate_access(db,user,candidate_id)
    s = db.query(Score).filter_by(candidate_id=c.id).order_by(desc(Score.created_at)).first()
    masked = user.role == "client"
    return {"id":c.id,"candidate_code":c.candidate_code,"name":c.name,"current_role":c.current_role,
            "experience_years":c.experience_years,"skills":c.skills,"notice_days":c.notice_days,
            "email":"Hidden" if masked else c.email,"phone":"Hidden" if masked else c.phone,
            "resume_text":c.resume_text if not masked else None,"consent_given":c.consent_given,
            "score":s.score if s else None,"evidence":s.evidence if s else []}

@app.post("/api/v1/candidates/{candidate_id}/submit")
def submit_candidate(candidate_id: int, client_id: str = Form("company-a"), db: Session = Depends(get_db), user: User = Depends(require_role("recruiter"))):
    c = db.get(Candidate,candidate_id)
    if not c or c.deleted: raise HTTPException(404,"Candidate not found")
    if not c.consent_given: raise HTTPException(400,"Candidate consent is required before sharing")
    sub = db.query(Submission).filter_by(candidate_id=c.id,job_id=c.job_id,client_id=client_id).first()
    if not sub:
        sub = Submission(candidate_id=c.id,job_id=c.job_id,client_id=client_id,status="submitted")
        db.add(sub); db.add(PipelineEvent(candidate_id=c.id,job_id=c.job_id,status="submitted",note="Shared with client"))
        db.commit()
    return {"success":True,"submission_id":sub.id,"status":sub.status}

@app.get("/api/v1/client/submissions")
def client_submissions(db: Session = Depends(get_db), user: User = Depends(require_role("client"))):
    subs = db.query(Submission).filter_by(client_id=user.client_id).order_by(desc(Submission.created_at)).all()
    result=[]
    for s in subs:
        c=db.get(Candidate,s.candidate_id); j=db.get(Job,s.job_id)
        if c and not c.deleted:
            score=db.query(Score).filter_by(candidate_id=c.id,job_id=j.id).first()
            result.append({"submission_id":s.id,"candidate_id":c.id,"candidate_code":c.candidate_code,
                           "name":c.name,"current_role":c.current_role,"experience_years":c.experience_years,
                           "skills":c.skills,"score":score.score if score else None,"job_title":j.title,
                           "status":s.status,"client_reason":s.client_reason})
    return result

@app.patch("/api/v1/client/submissions/{submission_id}")
def client_decision(submission_id: int, payload: ClientDecision, db: Session = Depends(get_db), user: User = Depends(require_role("client"))):
    sub=db.query(Submission).filter_by(id=submission_id,client_id=user.client_id).first()
    if not sub: raise HTTPException(404,"Submission not found")
    allowed={"shortlisted","rejected","interview_proposed"}
    if payload.status not in allowed: raise HTTPException(400,"Invalid client decision")
    if payload.status=="rejected" and not (payload.reason or "").strip():
        raise HTTPException(400,"A rejection reason is required")
    if payload.status=="interview_proposed" and not (payload.interview_slot or "").strip():
        raise HTTPException(400,"An interview slot is required")
    sub.status=payload.status; sub.client_reason=payload.reason; sub.interview_slot=payload.interview_slot
    db.add(PipelineEvent(candidate_id=sub.candidate_id,job_id=sub.job_id,status=payload.status,note=payload.reason or payload.interview_slot or "Client update"))
    db.commit()
    return {"success":True,"status":sub.status}

@app.get("/api/v1/pipeline")
def pipeline(db: Session = Depends(get_db), user: User = Depends(current_user)):
    events=db.query(PipelineEvent).order_by(desc(PipelineEvent.created_at)).all()
    if user.role=="client":
        allowed={s.candidate_id for s in db.query(Submission).filter_by(client_id=user.client_id).all()}
        events=[e for e in events if e.candidate_id in allowed]
    return [{"candidate_id":e.candidate_id,"job_id":e.job_id,"status":e.status,"note":e.note,"created_at":e.created_at.isoformat()} for e in events]

@app.delete("/api/v1/candidates/{candidate_id}")
def delete_candidate(candidate_id: int, db: Session = Depends(get_db), user: User = Depends(require_role("recruiter"))):
    c=db.get(Candidate,candidate_id)
    if not c: raise HTTPException(404,"Candidate not found")
    c.deleted=True; c.email=None; c.phone=None; c.resume_text="[DELETED AT CANDIDATE REQUEST]"
    c.resume_path=None
    db.query(Submission).filter_by(candidate_id=c.id).delete()
    db.add(PipelineEvent(candidate_id=c.id,job_id=c.job_id,status="deleted",note="Candidate deletion request processed"))
    db.commit()
    return {"success":True,"message":"Candidate profile data deleted or anonymized"}

@app.get("/api/v1/audit")
def audit(db: Session = Depends(get_db), user: User = Depends(require_role("recruiter"))):
    rows=db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(100).all()
    return [{"user_id":r.user_id,"action":r.action,"resource_type":r.resource_type,"resource_id":r.resource_id,"created_at":r.created_at.isoformat()} for r in rows]
