'''backend/auth.py'''
"""Authentication utilities including password hashing and session management."""
import os
from datetime import datetime, timedelta
import secrets
from fastapi import Request, HTTPException, status, Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session as DbSession
from pydantic import BaseModel

from .database import get_db
from .models_orm import User, Session

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class LoginRequest(BaseModel):
    username: str
    password: str

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_session(db: DbSession, user_id: int, days: int = 7) -> Session:
    """Create a new session in the database for the user."""
    expires = datetime.utcnow() + timedelta(days=days)
    new_session = Session(
        user_id=user_id,
        expires_at=expires
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    return new_session

def get_current_user(request: Request, db: DbSession = Depends(get_db)):
    """Dependency that extracts the user from the session cookie and verifies it against the DB."""
    session_id = request.cookies.get("session_id")
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: missing session cookie",
        )
    
    session_record = db.query(Session).filter(Session.id == session_id).first()
    if not session_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: invalid session",
        )
        
    if session_record.expires_at < datetime.utcnow():
        db.delete(session_record)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: session expired",
        )
        
    user = session_record.user
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: user not found",
        )
        
    return {"session_id": session_record.id, "user_id": user.id, "username": user.username}
