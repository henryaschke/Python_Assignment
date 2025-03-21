from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from typing import List

from Python_Assignment.database import get_db, get_user_by_email, User
from Python_Assignment.models.auth import UserCreate, User as UserModel, Token, LoginRequest
from Python_Assignment.auth.dependencies import (
    get_password_hash, 
    authenticate_user, 
    create_access_token,
    get_current_active_user, 
    ACCESS_TOKEN_EXPIRE_MINUTES
)

import logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.post("/register", response_model=UserModel, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user.
    """
    try:
        # Check if user already exists
        existing_user = get_user_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        db = get_db()
        hashed_password = get_password_hash(user_data.password)
        
        new_user_data = {
            "email": user_data.email,
            "hashed_password": hashed_password,
            "name": user_data.name,
            "created_at": datetime.now(),
            "is_active": True
        }
        
        # Insert user into database
        db.insert_row(User, new_user_data)
        
        # Get the created user
        created_user = get_user_by_email(user_data.email)
        if not created_user:
            logger.error("Failed to retrieve newly created user")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        # Log the created user structure to debug response validation
        logger.info(f"Created user data: {created_user}")
        
        # Make sure all required fields are present for UserModel response
        if "email" not in created_user or "User_ID" not in created_user:
            # Try to fix missing fields if possible
            if "email" not in created_user and "email" in new_user_data:
                created_user["email"] = new_user_data["email"]
                
            # Log the fixed user data
            logger.info(f"Fixed user data for response: {created_user}")
        
        return created_user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error in register_user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {str(e)}"
        )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["User_ID"])}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest):
    """
    Login endpoint for clients that don't support OAuth2 form data.
    """
    user = authenticate_user(login_data.email, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user["User_ID"])}, 
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserModel)
async def read_users_me(current_user = Depends(get_current_active_user)):
    """
    Get current user information.
    """
    return current_user 