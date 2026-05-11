from database import LocalSession, Base, engine
import schemas
from models import Company, Job, Applicant, Admin
from sqlalchemy.orm import Session
from fastapi import HTTPException, Depends
from datetime import datetime, timedelta
from key import key
from pwdlib import PasswordHash
import jwt
from config import settings

password_hash = PasswordHash.recommended()

def get_password_hash(password):
    return password_hash.hash(password)

def verify_password(plain_password, hashed_password):
    return password_hash.verify(plain_password, hashed_password)

def get_db():
    db=LocalSession()
    try:
        yield db
    finally:
        db.close()

def create_tables():
    Base.metadata.create_all(engine)

def sending_email(email:str):
    print(f"Sending email to {email}")

def create_company(company:schemas.CompanyUpdate, db: Session):
    db_user=db.query(Company).filter(Company.email==company.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Company already exists")

    hashed_password = get_password_hash(company.password)

    new_company=Company(
        name=company.name,
        email=company.email,
        website=company.website,
        location=company.location,
        password=hashed_password,
        created_at=datetime.now(),
    )
    db.add(new_company)
    db.commit()
    db.refresh(new_company)

    return new_company

def sign_in_company(company:schemas.CompanyLogin, db: Session):
    db_user=db.query(Company).filter(Company.email==company.email).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="email not found")

    if not verify_password(company.password, db_user.password):
        raise HTTPException(status_code=401, detail="incorrect password")

    exp_time=datetime.now()  + timedelta(days=settings.EXPIRE_TIME)

    token = jwt.encode({"_id":db_user.id, "exp":exp_time}, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    db_user.api_key=token
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def get_company_by_id(id: int, db: Session):
    db_user=db.query(Company).filter(Company.id==id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="company not found")
    return db_user

def update_company_changes(company: schemas.CompanyBase, db: Session, company_id: int):
    db_user=get_company_by_id(company_id, db)
    if db_user:
        new_dict=company.model_dump(exclude_unset=True)
        for key, value in new_dict.items():
            if value is not None:
                setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)

    return db_user

def remove_company(company_id: int,db: Session):
    db_user=get_company_by_id(company_id, db)
    if db_user:
        db.delete(db_user)
        db.commit()
        return db_user

def post_job(job: schemas.JobBase, db: Session, company_id: int):
    new_job=Job(**job.model_dump())
    new_job.company_id=company_id
    new_job.created_at=datetime.now()
    new_job.is_active=True
    db.add(new_job)
    db.commit()
    db.refresh(new_job)
    return new_job

def get_all_active_jobs(db:Session):
    active_jobs=db.query(Job).filter(Job.is_active==True).all()
    return active_jobs

def get_all_disabled_jobs(db:Session):
    disabled_jobs=db.query(Job).filter(Job.is_active==False).all()
    return disabled_jobs


def get_all_jobs_by_companyID(company_id: int, db: Session):
    company_job = db.query(Job).filter(Job.company_id == company_id).all()
    return company_job

def get_job_by_ID(id: int, db: Session):
    job=db.query(Job).filter(Job.id == id).first()
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job

def update_job_changes(job_id:int, job: schemas.UpdateJob, db: Session, company_id: int):
    current_job=db.query(Job).filter(Job.company_id == company_id).filter(Job.id == job_id).first()
    new_job=job.model_dump(exclude_unset=True)
    for key, value in new_job.items():
        if value is not None:
            setattr(current_job, key, value)

    db.commit()
    db.refresh(current_job)
    return current_job

def update_active_jobs_to_inactive(job_id, db, company_id):
    current_job=db.query(Job).filter(Job.company_id == company_id).filter(Job.id == job_id).first()
    if current_job.is_active==True:
        current_job.is_active=False
        db.add(current_job)
        db.commit()
    return current_job

def remove_job(job_id:int, db: Session, company_id: int):
    current_job=db.query(Job).filter(Job.company_id == company_id).filter(Job.id == job_id).first()
    db.delete(current_job)
    db.commit()
    return current_job


def search_jobs_by_location(location:str, db: Session):
    job_location=db.query(Job).filter(Job.location.ilike(location), Job.is_active==True).all()
    return job_location

def search_jobs_by_type(type:str, db: Session):
    job_type=db.query(Job).filter(Job.job_type==type, Job.is_active==True).all()
    return job_type

def search_jobs_by_title(title:str, db: Session):
    job_title=db.query(Job).filter(
            Job.title.ilike(f"%{title}%"),Job.is_active == True).all()

    return job_title

def filter_jobs_by_minimum_salary(salary_min:str, db: Session):
    min_salary=db.query(Job).filter(Job.salary_min>=salary_min, Job.is_active==True).all()
    return min_salary


def search_data_by_pagination(skip: int, limit: int, db: Session):
    active_jobs=db.query(Job).filter(Job.is_active==True).offset(skip).limit(limit).all()
    return active_jobs

def apply_for_job(
    job_id: int,
    applicant: schemas.ApplicationBase,
    db: Session,
    cv_path: str = None
):
    requested_job = get_job_by_ID(job_id, db)
    new_applicant = Applicant(
        **applicant.model_dump(),
        job_id=requested_job.id,
        status='pending',
        created_at=datetime.now(),
        cv_path=cv_path
    )
    db.add(new_applicant)
    db.commit()
    db.refresh(new_applicant)
    return new_applicant

def get_applications(job_id: int, db: Session):
    applications = db.query(Applicant).filter(Applicant.job_id == job_id).all()
    return applications

def get_application_by_ID(id: int, db: Session):
    application = db.query(Applicant).filter(Applicant.id == id).first()
    if not application:
        raise HTTPException(status_code=404, detail="application not found")
    return application

def get_job_applications(job_id: int, company_id: int, db: Session):
    current_job=get_job_by_ID(job_id, db)

    if current_job.company_id != company_id:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return get_applications(current_job.id, db)

def change_application_status(applicant_id: int, status: bool, company_id: int, db: Session,):
    current_application=get_application_by_ID(applicant_id, db)
    application_job_id=current_application.job_id
    job=get_job_by_ID(application_job_id, db)
    if job.company_id != company_id:
        raise HTTPException(status_code=403, detail="Invalid API key")
    if status is True:
        current_application.status = 'accepted'
    if status is False:
        current_application.status = 'rejected'
    db.add(current_application)
    db.commit()
    return current_application

def company_total_active_jobs(company_id:int, db: Session):
    active_jobs=db.query(Job).filter(Job.is_active==True, Job.company_id==company_id).count()
    return active_jobs

def company_total_disable_jobs(company_id:int, db: Session):
    active_jobs=db.query(Job).filter(Job.is_active==False, Job.company_id==company_id).count()
    return active_jobs

def company_job_ids(company_id:int, db: Session):
    company_jobs=db.query(Job).filter(Job.company_id==company_id).all()
    job_ids=[]
    for job in company_jobs:
        job_ids.append(job.id)

    return job_ids

def accepted_job_applications(job_id: int, db: Session):
    applications = db.query(Applicant).filter(Applicant.job_id == job_id, Applicant.status=='accepted').all()

    return applications

def company_total_accepted_applicants(company_id:int, db: Session):
    job_IDs=company_job_ids(company_id, db)
    accepted_applicants=[]
    total=0

    for id in job_IDs:
        applicants=accepted_job_applications(id, db)
        if applicants:
            accepted_applicants.append(applicants)
            total += len(applicants)

    # alternative solution:
    # db.query(Applicant).filter(
    #     Applicant.job_id.in_(job_ids),
    #     Applicant.status == "accepted"
    # ).count()

    return total


def company_total_rejected_applicants(company_id:int, db: Session):
    job_IDs=company_job_ids(company_id, db)

    return db.query(Applicant).filter(
        Applicant.job_id.in_(job_IDs),
        Applicant.status == "rejected"
    ).count()


def company_total_pending_applicants(company_id:int, db: Session):
    job_IDs=company_job_ids(company_id, db)

    return db.query(Applicant).filter(
        Applicant.job_id.in_(job_IDs),
        Applicant.status == "pending"
    ).count()



def viewStats(company_id: int, db: Session):
    active_jobs=company_total_active_jobs(company_id, db)
    disable_jobs=company_total_disable_jobs(company_id, db)
    accepted_applicants=company_total_accepted_applicants(company_id, db)
    rejected_applicants=company_total_rejected_applicants(company_id, db)
    pending_applicants=company_total_pending_applicants(company_id, db)

    return {
        'total_jobs' : active_jobs + disable_jobs,
        'active_jobs': active_jobs,
        'disabled_jobs': disable_jobs,
        'total_applications': accepted_applicants + rejected_applicants + pending_applicants ,
        'total_accepted_applications': accepted_applicants,
        'total_rejected_applications': rejected_applicants,
        'total_pending_applications': pending_applicants
    }

def sign_in_admin(admin: schemas.AdminBase, db: Session):
    db_admin=db.query(Admin).filter(Admin.email==admin.email).first()
    if not db_admin:
        raise HTTPException(status_code=404, detail="Admin not found")
    if db_admin.password != admin.password:
        raise HTTPException(status_code=401, detail="Password not found")

    db_admin.api_key = key()
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def total_companies(db: Session):
    companies=db.query(Company).count()
    return companies

def total_active_jobs(db: Session):
    active_jobs=db.query(Job).filter(Job.is_active==True).count()
    return active_jobs
def total_disable_jobs(db: Session):
    disable_jobs=db.query(Job).filter(Job.is_active==False).count()
    return disable_jobs

def total_accepted_applicants(db: Session):
    accepted_applicants= db.query(Applicant).filter(Applicant.status=='accepted').count()
    return accepted_applicants
def total_rejected_applicants(db: Session):
    rejected_applicants=db.query(Applicant).filter(Applicant.status=='rejected').count()
    return rejected_applicants
def total_pending_applicants(db: Session):
    pending_applicants=db.query(Applicant).filter(Applicant.status=='pending').count()
    return pending_applicants

def viewAdminStats(db: Session):

    companies=total_companies(db)
    active_jobs=total_active_jobs(db)
    disable_jobs=total_disable_jobs(db)
    accepted_applicants=total_accepted_applicants(db)
    rejected_applicants=total_rejected_applicants(db)
    pending_applicants=total_pending_applicants(db)

    return {
        'total_companies':companies,
        'total_jobs' : active_jobs + disable_jobs,
        'active_jobs': active_jobs,
        'disabled_jobs': disable_jobs,
        'total_applications': accepted_applicants + rejected_applicants + pending_applicants,
        'accepted_applicants': accepted_applicants,
        'rejected_applicants': rejected_applicants,
        'pending_applicants': pending_applicants
    }










