from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session

import logging
from passlib.context import CryptContext

from database import get_session, get_user_by_email, get_user_by_id

# Configure logging
logger = logging.getLogger(__name__)

# Authentication constants
SECRET_KEY = "CHANGE_THIS_IN_PRODUCTION_ENVIRONMENT"  # Change this in production!
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # 1 hour token validity

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def verify_password(plain_password, hashed_password):
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """Generate a password hash."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(email: str, password: str):
    """Authenticate a user by email and password."""
    user = get_user_by_email(email)
    if not user:
        logger.warning(f"Authentication failed: User with email {email} not found")
        return False
    
    # Try to get password with different possible key names
    password_keys = ["hashed_password", "password", "hash", "password_hash"]
    hashed_password = None
    
    for key in password_keys:
        if key in user:
            hashed_password = user[key]
            break
    
    if not hashed_password:
        logger.error(f"Authentication failed: No password field found in user dict. Available keys: {list(user.keys())}")
        return False
    
    if not verify_password(password, hashed_password):
        logger.warning(f"Authentication failed: Invalid password for user {email}")
        return False
    
    return user

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """Get the current user from the JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Token validation failed: Missing subject (user_id)")
            raise credentials_exception
    except JWTError as e:
        logger.warning(f"Token validation failed: JWT Error - {str(e)}")
        raise credentials_exception
    
    # Convert string user_id to int
    try:
        user_id_int = int(user_id)
    except ValueError:
        logger.warning(f"Token validation failed: Invalid user ID format - {user_id}")
        raise credentials_exception
    
    user = get_user_by_id(user_id_int)
    if user is None:
        logger.warning(f"Token validation failed: User ID {user_id} not found")
        raise credentials_exception
    
    return user

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Check if the current user is active."""
    if not current_user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

def get_db_session():
    """Get a database session dependency."""
    session = get_session()
    try:
        yield session
    finally:
        session.close() 