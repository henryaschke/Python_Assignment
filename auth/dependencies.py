from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

import logging
from passlib.context import CryptContext

from Python_Assignment.database import get_session, get_user_by_email, get_user_by_id

# Configure logging
logger = logging.getLogger(__name__)

# Authentication constants
SECRET_KEY = "CHANGE_THIS_IN_PRODUCTION_ENVIRONMENT"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour token validity

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme for token handling
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(email: str, password: str):
    try:
        # Get user by email
        user = get_user_by_email(email)
        if not user:
            logger.warning(f"User with email {email} not found")
            return None
        
        # Verify password
        if not verify_password(password, user.get("hashed_password", "")):
            logger.warning(f"Password verification failed for user {email}")
            return None
        
        # Return user data
        return {
            "User_ID": user.get("User_ID"),
            "email": user.get("email"),
            "name": user.get("name"),
            "is_active": user.get("is_active", True)
        }
    
    except Exception as e:
        logger.error(f"Error in authenticate_user: {e}")
        return None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        # Verify token and extract payload
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            logger.warning("Token payload missing subject field")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user data
        user = get_user_by_id(int(user_id))
        if user is None:
            logger.warning(f"User with ID {user_id} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Return user data
        return {
            "User_ID": user.get("User_ID"),
            "email": user.get("email"),
            "name": user.get("name"),
            "is_active": user.get("is_active", True)
        }
    
    except JWTError as e:
        logger.error(f"JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(current_user = Depends(get_current_user)):
    if not current_user.get("is_active", False):
        logger.warning(f"Inactive user attempting to access resource: {current_user.get('email')}")
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

def get_db_session():
    db_session = get_session()
    try:
        yield db_session
    finally:
        db_session.close() 