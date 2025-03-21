from fastapi import APIRouter, BackgroundTasks, Query, Depends, HTTPException
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

from Python_Assignment.models.battery import BatteryStatus, BatteryUpdate
from Python_Assignment.auth.dependencies import get_current_active_user
from Python_Assignment.database import get_battery_status, create_trade, update_battery_level, create_battery_if_not_exists

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.get("/status", response_model=Dict[str, Any])
async def get_battery_status_api(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get current battery status and capacity."""
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Getting battery status for authenticated user_id: {user_id}")
        
        battery = get_battery_status(user_id)
        if battery:
            # Get the battery status fields
            current_level = battery.get("current_level", 50.0)
            capacity = battery.get("capacity", 100.0)
            current_energy = battery.get("current_energy", 50.0)
            remaining_capacity = battery.get("remaining_capacity", 50.0)
            
            # Log the battery status for debugging
            logger.info(f"Battery status for user {user_id}: {battery}")
            
            return {
                "level": current_level,
                "capacity": {
                    "total": capacity,
                    "used": current_energy,
                    "remaining": remaining_capacity,
                    "percentage": current_level
                }
            }
        else:
            # Create a new battery if not found
            logger.info(f"No battery found for user {user_id}. Creating a new one.")
            battery = create_battery_if_not_exists(user_id)
            if not battery or "error" in battery:
                raise HTTPException(status_code=500, detail="Failed to create battery for user")
                
            # Return the newly created battery info
            return {
                "level": battery.get("current_level", 50.0),
                "capacity": {
                    "total": battery.get("capacity", 100.0),
                    "used": battery.get("current_energy", 50.0),
                    "remaining": battery.get("remaining_capacity", 50.0),
                    "percentage": battery.get("current_level", 50.0)
                }
            }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting battery status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history", response_model=List[Dict[str, Any]])
async def get_battery_history(
    days: int = Query(7, description="Number of days of history"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get battery level history (sample/dummy data)."""
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Getting battery history for authenticated user_id: {user_id}")
        
        today = datetime.now()
        # In a real app, you would query a BatteryHistory table here
        # For now we'll just return synthetic data
        return [
            {
                "time": (today - timedelta(hours=i)).isoformat(),
                "level": 50 + (10 * (i % 5 - 2))
            }
            for i in range(24 * days)
        ]
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting battery history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/charge", response_model=Dict[str, Any])
async def charge_battery(
    request: BatteryUpdate,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Charge the battery by a certain percentage."""
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Charging battery for authenticated user_id: {user_id}")
        
        battery = get_battery_status(user_id)
        if not battery:
            battery = create_battery_if_not_exists(user_id)
            if not battery or "error" in battery:
                raise HTTPException(status_code=500, detail="Failed to create battery for user")
        
        current_level = battery.get("current_level", 50.0)
        new_level = current_level + request.current_level
        
        # Cap at 100%
        if new_level > 100:
            new_level = 100
        
        # Update the battery level in the database
        update_success = update_battery_level(user_id, new_level)
        if not update_success:
            logger.error(f"Failed to update battery level for user {user_id}")
            raise HTTPException(status_code=500, detail="Failed to update battery level")
        
        # Create a "charge" trade record
        charge_amount = request.current_level
        trade_data = {
            "User_ID": user_id,
            "type": "charge",
            "quantity": charge_amount,
            "price": 0,
            "status": "executed",
            "execution_time": datetime.now(),
            "executed_at": datetime.now(),
            "created_at": datetime.now(),
            "resolution": 60,
            "market": "Battery"
        }
        create_trade(trade_data)
        
        return {
            "success": True, 
            "message": f"Battery charged by {charge_amount}%", 
            "newLevel": new_level
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error charging battery: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/discharge", response_model=Dict[str, Any])
async def discharge_battery(
    request: BatteryUpdate,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Discharge the battery by a certain percentage."""
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Discharging battery for authenticated user_id: {user_id}")
        
        battery = get_battery_status(user_id)
        if not battery:
            battery = create_battery_if_not_exists(user_id)
            if not battery or "error" in battery:
                raise HTTPException(status_code=500, detail="Failed to create battery for user")
        
        current_level = battery.get("current_level", 50.0)
        discharge_amount = request.current_level
        new_level = current_level - discharge_amount
        
        # Cap at 0%
        if new_level < 0:
            new_level = 0
        
        # Update the battery level in the database
        update_success = update_battery_level(user_id, new_level)
        if not update_success:
            logger.error(f"Failed to update battery level for user {user_id}")
            raise HTTPException(status_code=500, detail="Failed to update battery level")
        
        # Create a "discharge" trade record
        trade_data = {
            "User_ID": user_id,
            "type": "discharge",
            "quantity": discharge_amount,
            "price": 0,
            "status": "executed",
            "execution_time": datetime.now(),
            "executed_at": datetime.now(),
            "created_at": datetime.now(),
            "resolution": 60,
            "market": "Battery"
        }
        create_trade(trade_data)
        
        return {
            "success": True, 
            "message": f"Battery discharged by {discharge_amount}%", 
            "newLevel": new_level
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error discharging battery: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 