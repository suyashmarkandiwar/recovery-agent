from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, select
from pydantic import BaseModel
from app.db.database import get_session
from app.db.models import Employee
from app.security import verify_password, create_access_token
from app.config import ENVIRONMENT

router = APIRouter()

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(login_data: LoginRequest, response: Response, session: Session = Depends(get_session)):
    employee = session.exec(select(Employee).where(Employee.username == login_data.username)).first()
    
    if not employee or not verify_password(login_data.password, employee.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    access_token = create_access_token(data={"sub": str(employee.id)})
    is_prod = ENVIRONMENT == "PROD"
    
    # Conditionally setting the cookie as discussed in your diagram!
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        max_age=5 * 3600, 
        samesite="none" if is_prod else "lax",
        secure=is_prod
    )
    
    return {"message": "Login successful"}

@router.post("/logout")
def logout(response: Response):
    is_prod = ENVIRONMENT == "PROD"
    response.delete_cookie(
        key="access_token", 
        samesite="none" if is_prod else "lax", 
        secure=is_prod
    )
    return {"message": "Logged out successfully"}