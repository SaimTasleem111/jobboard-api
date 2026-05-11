from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from database import Base

class Company(Base):
    __tablename__ = 'company'
    id= Column(Integer, primary_key=True)
    name=Column(String)
    email=Column(String)
    password=Column(String)
    website=Column(String)
    location=Column(String)
    created_at=Column(DateTime)
    api_key=Column(String, unique=True)


class Job(Base):
    __tablename__ = 'job'
    id= Column(Integer, primary_key=True)
    title=Column(String)
    description=Column(String)
    salary_min=Column(Integer)
    salary_max=Column(Integer)
    location=Column(String)
    job_type=Column(String)
    company_id=Column(Integer, ForeignKey('company.id'))
    is_active=Column(Boolean)
    created_at=Column(DateTime)

class Applicant(Base):
    __tablename__ = 'applicant'
    id= Column(Integer, primary_key=True)
    job_id=Column(Integer, ForeignKey('job.id'))
    applicant_name=Column(String)
    applicant_email=Column(String)
    cover_letter=Column(String)
    cv_path = Column(String, nullable=True)
    status=Column(String)
    created_at=Column(DateTime)


class Admin(Base):
    __tablename__ = 'admin'
    id= Column(Integer, primary_key=True)
    email=Column(String)
    password=Column(String)
    api_key=Column(String, unique=True)








