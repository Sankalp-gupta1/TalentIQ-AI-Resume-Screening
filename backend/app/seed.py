from app.database import Base, engine, SessionLocal
from app.models import User, Job, Candidate, Score, PipelineEvent
from app.auth import hash_password
from app.scoring import score_candidate

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    if not db.query(User).filter_by(email="recruiter@talentiq.demo").first():
        recruiter = User(name="Demo Recruiter", email="recruiter@talentiq.demo", password_hash=hash_password("TalentIQDemo!23"), role="recruiter")
        client = User(name="Demo Hiring Manager", email="client@talentiq.demo", password_hash=hash_password("TalentIQDemo!23"), role="client", client_id="company-a")
        db.add_all([recruiter, client]); db.commit()
        db.refresh(recruiter)
        job = Job(title="Senior Java Developer", company="Company A", location="Noida",
                  description="Senior Java Developer, 5-8 years, Java, Spring Boot, Microservices, Noida, notice up to 60 days.",
                  min_experience=5, max_experience=8, required_skills=["Java", "Spring Boot", "Microservices"],
                  max_notice_days=60, ctc="As per company band", created_by=recruiter.id)
        db.add(job); db.commit(); db.refresh(job)
        samples = [
            ("CND-91022","Ritika Bansal","Senior Java Developer",6.5,["Java","Spring Boot","Microservices"],60,
             "Ritika Bansal\nSenior Java Developer\n6.5 years experience building Java applications using Spring Boot and microservices. Notice period 60 days. Noida."),
            ("CND-91047","Arjun Rawat","KYC Analyst",3.0,["KYC","AML","Excel"],30,
             "Arjun Rawat\nKYC Analyst\n3 years experience in KYC, AML checks and Excel. Notice period 30 days."),
            ("CND-91088","Pooja Nair","Java Developer",4.0,["Java","Hibernate","REST API"],90,
             "Pooja Nair\nJava Developer\n4 years experience with Java, Hibernate and REST APIs. Notice period 90 days.")
        ]
        for code,name,role,exp,skills,notice,txt in samples:
            c = Candidate(candidate_code=code,name=name,current_role=role,experience_years=exp,skills=skills,
                          notice_days=notice,location="Noida" if code!="CND-91047" else "Delhi",
                          resume_text=txt,job_id=job.id,consent_given=True)
            db.add(c); db.commit(); db.refresh(c)
            result = score_candidate(c,job)
            db.add(Score(candidate_id=c.id,job_id=job.id,**result))
            db.add(PipelineEvent(candidate_id=c.id,job_id=job.id,status="screened",note="Seeded demo candidate"))
        db.commit()
        print("Seeded TalentIQ demo users, job and candidates.")
    else:
        print("Demo data already exists.")
finally:
    db.close()
