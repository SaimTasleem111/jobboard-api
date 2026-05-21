from pydantic import BaseModel, Field, model_validator, field_validator
from datetime import datetime
from typing import Optional, Dict, List, Annotated

class AdminBase(BaseModel):
    email: str
    password: str

class AdminInformation(BaseModel):
    id: int
    email: str
    api_key: str

class CompanyBase(BaseModel):
    name: str
    email: str
    website: str
    location: str
    password: str

class CompanyInformation(BaseModel):
    id: int
    name: str
    email: str
    website: str
    location: str
    created_at: datetime

class CompanyLogin(BaseModel):
    email: str
    password: str

class CompanyLoginInformation(BaseModel):
    email: str
    name:str
    api_key: str

class CompanyUpdate(BaseModel):
   name: Annotated[Optional[str],Field(description='name')]=None
   email: Annotated[Optional[str],Field(description='email')]=None
   website: Annotated[Optional[str],Field(description='website')]=None
   location: Annotated[Optional[str],Field(description='location')]=None
   password: Annotated[Optional[str],Field(description='password')]=None

class JobBase(BaseModel):
    title: str
    description: str
    salary_min: int
    salary_max: int
    job_type: str
    location: str



    @model_validator(mode='after')
    def salary_min_validator(cls, self):
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
                raise ValueError('salary_min must be less than salary_max')

        return self

class UpdateJob(BaseModel):
    title: Annotated[Optional[str],Field(description='title')]=None
    description: Annotated[Optional[str],Field(description='description')]=None
    salary_min: Annotated[Optional[int],Field(description='salary_min',gt=10000)]=None
    salary_max: Annotated[Optional[int],Field(description='salary_max',gt=10000)]=None
    job_type: Annotated[Optional[str],Field(description='job_type')]=None
    location: Annotated[Optional[str],Field(description='location')]=None

    @model_validator(mode='after')
    def salary_min_validator(cls, self):
        if self.salary_min is not None and self.salary_max is not None:
            if self.salary_min > self.salary_max:
             raise ValueError('salary_min must be less than salary_max')

        return self


class JobInformation(BaseModel):
    id: int
    title: str
    description: str
    salary_min: int
    salary_max: int
    job_type: str
    location: str
    company_id: int
    created_at: datetime
    is_active: bool

class ApplicationBase(BaseModel):
    applicant_name: str
    applicant_email: str
    cover_letter: str

class ApplicationInformation(BaseModel):
    id: int
    job_id: int
    applicant_name: str
    applicant_email: str
    cover_letter: str
    cv_path: str | None = None
    status: str
    created_at: datetime
    ai_score: int | None = None
    ai_qualifications: str | None = None
    ai_job_history: str | None = None
    ai_skill_set: str | None = None
    ai_justification: str | None = None
    ai_analyzed: bool = False

class AIAnalysisResult(BaseModel):
    applicant_id: int
    score: int
    qualifications: str
    job_history: str
    skill_set: str
    justification: str

    class Config:
        from_attributes = True