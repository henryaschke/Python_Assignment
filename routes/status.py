from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any
from datetime import datetime
import platform
import sqlite3
import os

from Python_Assignment.database import test_db_connection
from Python_Assignment.auth.dependencies import get_current_active_user

import logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.get("/status", response_model=Dict[str, Any])
async def get_status():
    """
    Get server status and diagnostic information.
    """
    db_connected = test_db_connection()
    
    # Get SQLite version
    sqlite_version = sqlite3.version
    
    # Check if database file exists
    db_file_path = "energy_trading.db"
    db_file_exists = os.path.exists(db_file_path)
    db_file_size = os.path.getsize(db_file_path) if db_file_exists else 0
    
    return {
        "status": "operational" if db_connected else "degraded",
        "timestamp": datetime.now().isoformat(),
        "database": {
            "connected": db_connected,
            "type": "SQLite",
            "version": sqlite_version,
            "file_exists": db_file_exists,
            "file_size_bytes": db_file_size
        },
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "processor": platform.processor()
        }
    }

@router.get("/whoami", response_model=Dict[str, Any])
async def who_am_i(current_user = Depends(get_current_active_user)):
    """
    Get information about the authenticated user.
    """
    return {
        "user_id": current_user["User_ID"],
        "email": current_user["email"],
        "name": current_user.get("name", "Anonymous"),
        "is_active": current_user.get("is_active", True),
        "timestamp": datetime.now().isoformat()
    } 