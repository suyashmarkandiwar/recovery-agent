from fastapi import Request, HTTPException, Depends
from sqlmodel import Session, select
from jose import jwt, JWTError
from app.db.database import get_session
from app.db.models import Employee
from app.config import JWT_SECRET, JWT_ALGORITHM

def get_current_employee(request: Request, session: Session = Depends(get_session)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        employee_id: int = payload.get("sub")
        if employee_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    employee = session.exec(select(Employee).where(Employee.id == employee_id)).first()
    if not employee:
        raise HTTPException(status_code=401, detail="Employee not found")
        
    return employee