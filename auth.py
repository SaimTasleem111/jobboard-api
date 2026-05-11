from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from models import Company, Admin
from operations import get_db
from fastapi import Depends, HTTPException, Security
from config import settings

api_key_header = APIKeyHeader(name="X-API-Key")

def get_current_company(api_key=Security(api_key_header), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(api_key, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except ExpiredSignatureError:
        raise HTTPException(status_code=403, detail="Token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=403, detail="Invalid token")

    company = db.query(Company).filter_by(api_key=api_key).first()

    if not company:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return company

def get_current_admin(api_key= Security(api_key_header), db=Depends(get_db)):
    admin = db.query(Admin).filter_by(api_key=api_key).first()
    if not admin:
        raise HTTPException(
            status_code=403,
            detail="Invalid API key"
        )
    return admin



