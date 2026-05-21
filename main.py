from fastapi import FastAPI, Depends, BackgroundTasks, File, UploadFile, Form, HTTPException
from schemas import CompanyBase, CompanyInformation, CompanyUpdate, CompanyLogin,CompanyLoginInformation, JobBase, UpdateJob, JobInformation, ApplicationBase, ApplicationInformation, AdminBase,AdminInformation, AIAnalysisResult
from operations import create_tables, get_db, create_company, sign_in_company, get_company_by_id, update_company_changes, remove_company,post_job, get_all_active_jobs, get_all_jobs_by_companyID, get_job_by_ID, update_job_changes, remove_job, update_active_jobs_to_inactive, search_jobs_by_location, search_jobs_by_type, search_jobs_by_title, filter_jobs_by_minimum_salary, search_data_by_pagination, apply_for_job, get_job_applications, change_application_status, viewStats, sign_in_admin, viewAdminStats, sending_email
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from auth import get_current_company, get_current_admin
from typing import List
import shutil
import os
import httpx
import models
from fastapi.staticfiles import StaticFiles


app = FastAPI()
os.makedirs("uploads", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "https://jobboard-frontend-bk4o.onrender.com"
    ],    
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
BASE_URL = os.getenv("BASE_URL", "http://localhost:8000")

async def send_to_n8n(
    applicant_id: int,
    cv_path: str,
    job_title: str,
    job_description: str
):
    cv_url = f"{BASE_URL}/{cv_path}"
    payload = {
        "applicant_id": applicant_id,
        "cv_url": cv_url,
        "job_title": job_title,
        "job_description": job_description
    }
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                N8N_WEBHOOK_URL,
                json=payload,
                timeout=30
            )
    except Exception as e:
        print(f"n8n webhook error: {e}")

create_tables()

@app.get("/")
async def root():
    return {"JOB BOARD"}

@app.post("/companies/register", response_model=CompanyInformation, status_code=201)
def register_company(company: CompanyBase, db: Session = Depends(get_db)):
    return create_company(company, db)

@app.post("/companies/login", response_model=CompanyLoginInformation)
def login_company(company: CompanyLogin, db: Session= Depends(get_db)):
    return sign_in_company(company, db)

@app.get("/companies/{id}", response_model=CompanyInformation)
def get_company(id: int, db: Session = Depends(get_db)):
    return get_company_by_id(id, db)

@app.put("/companies/{id}", response_model=CompanyInformation)
def update_company(company: CompanyUpdate, db: Session = Depends(get_db), current_company: int = Depends(get_current_company)):
    return update_company_changes(company, db,current_company.id )

@app.delete("/companies/{id}")
def delete_company(current_company: int = Depends(get_current_company), db: Session = Depends(get_db)):
    return remove_company(current_company.id, db)

@app.post("/jobs", response_model=JobInformation, status_code=201)
def create_job(job: JobBase, db: Session = Depends(get_db), current_company: int = Depends(get_current_company)):
    return post_job(job, db,current_company.id)

@app.get("/jobs/", response_model=List[JobInformation])
def get_jobs(location: str | None = None, job_type: str | None= None, job_title: str | None= None ,salary_min: int | None=None, limit: int | None = None, skip: int | None = None,db: Session = Depends(get_db)):

    if location:
        return search_jobs_by_location(location, db)

    elif job_type:
        return search_jobs_by_type(job_type, db)

    elif job_title:
        return search_jobs_by_title(job_title, db)

    elif salary_min:
        return filter_jobs_by_minimum_salary(salary_min, db)

    elif limit and skip is not None:
        return search_data_by_pagination(skip, limit, db)

    return get_all_active_jobs(db)

@app.get("/companies/jobs/{id}", response_model=List[JobInformation])
def get_job(id: int, db: Session = Depends(get_db)):
    return get_all_jobs_by_companyID(id, db)

@app.get("/job/{id}", response_model=JobInformation)
def get_job_by_id(id: int, db: Session = Depends(get_db)):
    return get_job_by_ID(id, db)

@app.put("/jobs/{id}", response_model=JobInformation)
def update_job(id: int, job: UpdateJob, db: Session = Depends(get_db),current_company:int = Depends(get_current_company)):
    return update_job_changes(id, job, db, current_company.id)

@app.delete("/jobs/{id}")
def delete_job(id: int, db: Session = Depends(get_db),current_company:int = Depends(get_current_company)):
    return remove_job(id, db, current_company.id)

@app.patch("/jobs/{id}/close", response_model=JobInformation)
def update_job_status(id: int, db: Session = Depends(get_db),current_company:int = Depends(get_current_company)):
    return update_active_jobs_to_inactive(id, db, current_company.id)

@app.post("/jobs/{id}/apply", response_model=schemas.ApplicationInformation, status_code=201)
async def job_apply(
    id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    applicant_name: str = Form(...),
    applicant_email: str = Form(...),
    cover_letter: str = Form(...),
    cv: UploadFile = File(None)
):
    cv_path = None
    if cv and cv.filename:
        os.makedirs("uploads", exist_ok=True)
        cv_path = f"uploads/{cv.filename}"
        with open(cv_path, "wb") as buffer:
            shutil.copyfileobj(cv.file, buffer)

    applicant = ApplicationBase(
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        cover_letter=cover_letter
    )
    application = apply_for_job(id, applicant, db, cv_path)

    background_tasks.add_task(sending_email, applicant_email)

    # NEW — send to n8n if CV was uploaded
    if cv_path and N8N_WEBHOOK_URL:
        job = get_job_by_ID(id, db)
        background_tasks.add_task(
            send_to_n8n,
            application.id,
            cv_path,
            job.title,
            job.description
        )

    return application

@app.get("/jobs/{id}/applications", response_model=List[ApplicationInformation])
def get_applications(id: int, current_company:int = Depends(get_current_company), db: Session = Depends(get_db)):
    return get_job_applications(id, current_company.id, db)

@app.patch("/applications/{id}/status", response_model=ApplicationInformation)
def update_application_status(applicant_id: int , status: bool,  current_company:int = Depends(get_current_company), db: Session = Depends(get_db)):
    return change_application_status(applicant_id, status, current_company.id, db)

@app.get("/companies/{id}/stats")
def get_stats(current_company:int = Depends(get_current_company), db: Session = Depends(get_db)):
    return viewStats(current_company.id, db)

@app.post("/admin/login", response_model=AdminInformation)
def admin_login(admin: AdminBase, db: Session = Depends(get_db)):
    return sign_in_admin(admin, db)

@app.get("/admin/stats")
def get_stats(current_admin:int = Depends(get_current_admin), db: Session = Depends(get_db)):
    return viewAdminStats(db)


@app.post("/applications/ai-result")
def receive_ai_result(
    result: AIAnalysisResult,
    db: Session = Depends(get_db)
):
    application = db.query(models.Applicant).filter(
        models.Applicant.id == result.applicant_id
    ).first()

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    application.ai_score = result.score
    application.ai_qualifications = result.qualifications
    application.ai_job_history = result.job_history
    application.ai_skill_set = result.skill_set
    application.ai_justification = result.justification
    application.ai_analyzed = True

    db.commit()
    return {"message": "AI analysis saved"}