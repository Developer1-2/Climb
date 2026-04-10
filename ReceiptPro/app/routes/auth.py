from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    phone: str


class LoginResponse(BaseModel):
    user_id: int
    is_paid: bool


@router.post("/login", response_model=LoginResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login or register user by phone number.
    If user doesn't exist, create a new one.
    """
    # Check if user exists
    user = db.query(User).filter(User.phone == request.phone).first()
    
    # Create new user if doesn't exist
    if not user:
        user = User(phone=request.phone)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return LoginResponse(user_id=user.id, is_paid=user.is_paid)
