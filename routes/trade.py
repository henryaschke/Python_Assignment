from fastapi import APIRouter, Depends, HTTPException, Body, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import uuid
import math
import random
from pydantic import BaseModel, Field, validator

from Python_Assignment.auth.dependencies import get_current_active_user
from Python_Assignment.database import get_db, Trade, create_trade, get_user_trades, update_trade_status, get_battery_status, update_battery_level, get_current_market_price, update_portfolio_balance, create_battery_if_not_exists
from Python_Assignment.models.trade import TradeRequest, TradeResponse, TradeStatusUpdate

# Setup logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Define request model for buy/sell operations
class ElectricityTradeRequest(BaseModel):
    quantity: float = Field(..., description="Amount of electricity to buy/sell in kWh")
    price: Optional[float] = Field(None, description="Price per kWh (optional, will use current market price if not provided)")
    
    @validator('quantity')
    def quantity_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        return v

# Get all trades for a user
@router.get("/", response_model=List[Dict[str, Any]])
async def get_trades(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get all trades for the authenticated user with optional date filtering."""
    try:
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
        
        logger.info(f"Getting trades for user {user_id}")
        
        # Convert date strings to datetime objects if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid start_date format: {start_date}")
                raise HTTPException(status_code=400, detail="Invalid start_date format")
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                logger.warning(f"Invalid end_date format: {end_date}")
                raise HTTPException(status_code=400, detail="Invalid end_date format")
        
        # Use database function to get trades
        # Limit and offset are not part of the function signature, so we ignore them
        trades = get_user_trades(user_id, start_datetime, end_datetime)
        
        # Apply limit and offset in memory
        if trades:
            trades = trades[offset:offset+limit]
            
            # Clean up duplicate fields in the response
            cleaned_trades = []
            for trade in trades:
                # Remove lowercase duplicates
                if 'trade_id' in trade and 'Trade_ID' in trade:
                    del trade['trade_id']
                if 'user_id' in trade and 'User_ID' in trade:
                    del trade['user_id']
                cleaned_trades.append(trade)
            
            return cleaned_trades
        
        return []
    except HTTPException:
        # Re-raise HTTP exceptions
        raise 
    except Exception as e:
        logger.error(f"Error retrieving trades: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving trades: {str(e)}")

# Buy electricity endpoint
@router.post("/buy", response_model=Dict[str, Any])
async def buy_electricity(
    request: ElectricityTradeRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Buying electricity for user {user_id}: {request.quantity} kWh")
        
        # Get battery status
        battery = get_battery_status(user_id)
        if not battery:
            battery = create_battery_if_not_exists(user_id)
            if not battery or "error" in battery:
                raise HTTPException(status_code=500, detail="Failed to get or create battery")
        
        # Check if we have enough free capacity in the battery
        current_level = battery.get("current_level", 0)
        capacity = battery.get("capacity", 100.0)
        current_energy = (current_level / 100.0) * capacity
        remaining_capacity = capacity - current_energy
        
        if request.quantity > remaining_capacity:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough capacity in battery. Can only store {remaining_capacity:.2f} kWh more"
            )
        
        # Get current market price if not provided
        price = request.price
        if price is None:
            # Get current market price
            db = get_db()
            
            # Create a function to get the current market price
            def get_current_price(session):
                # This is a simple implementation - in a real system, you'd get the actual market price 
                # from a market data service or API
                now = datetime.now()
                current_hour = now.hour
                
                # Calculate a synthetic price
                base_price = 50 + 10 * math.sin(current_hour / 12 * math.pi)
                variation = random.uniform(-5, 5)
                return base_price + variation
            
            # Use the database helper to execute the function
            try:
                import random
                import math
                price = get_current_price(None)  # The session is managed internally
                price = round(price, 2)
            except Exception as e:
                logger.error(f"Error getting current price: {e}")
                price = 45.0  # Default price if we can't get the current price
        
        # Calculate new battery level
        energy_increase = request.quantity
        percentage_increase = (energy_increase / capacity) * 100
        new_level = min(current_level + percentage_increase, 100.0)  # Cap at 100%
        
        # Update battery level
        update_success = update_battery_level(user_id, new_level)
        if not update_success:
            raise HTTPException(status_code=500, detail="Failed to update battery level")
        
        # Create a trade record
        total_cost = request.quantity * price
        trade_data = {
            "User_ID": user_id,
            "type": "buy",
            "quantity": request.quantity,
            "price": price,
            "status": "executed",
            "execution_time": datetime.now(),
            "executed_at": datetime.now(),
            "created_at": datetime.now(),
            "resolution": 60,  # 1 hour resolution
            "market": "Electricity"
        }
        
        trade_created = create_trade(trade_data)
        if not trade_created:
            logger.error(f"Failed to create trade record for user {user_id}")
            # Continue anyway since the battery has been updated
        
        return {
            "success": True,
            "message": f"Successfully bought {request.quantity} kWh of electricity at {price} per kWh",
            "total_cost": total_cost,
            "new_battery_level": new_level,
            "trade_executed": datetime.now().isoformat()
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error buying electricity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Sell electricity endpoint
@router.post("/sell", response_model=Dict[str, Any])
async def sell_electricity(
    request: ElectricityTradeRequest,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Selling electricity for user {user_id}: {request.quantity} kWh")
        
        # Get battery status
        battery = get_battery_status(user_id)
        if not battery:
            battery = create_battery_if_not_exists(user_id)
            if not battery or "error" in battery:
                raise HTTPException(status_code=500, detail="Failed to get or create battery")
        
        # Check if we have enough energy in the battery to sell
        current_level = battery.get("current_level", 0)
        capacity = battery.get("capacity", 100.0)
        current_energy = (current_level / 100.0) * capacity
        
        if request.quantity > current_energy:
            raise HTTPException(
                status_code=400, 
                detail=f"Not enough energy in battery. Only have {current_energy:.2f} kWh available"
            )
        
        # Get current market price if not provided
        price = request.price
        if price is None:
            # Get current market price
            db = get_db()
            
            # Create a function to get the current market price
            def get_current_price(session):
                # This is a simple implementation - in a real system, you'd get the actual market price
                # from a market data service or API
                now = datetime.now()
                current_hour = now.hour
                
                # Calculate a synthetic price
                base_price = 50 + 10 * math.sin(current_hour / 12 * math.pi)
                variation = random.uniform(-5, 5)
                return base_price + variation
            
            # Use the database helper to execute the function
            try:
                import random
                import math
                price = get_current_price(None)  # The session is managed internally
                price = round(price, 2)
            except Exception as e:
                logger.error(f"Error getting current price: {e}")
                price = 45.0  # Default price if we can't get the current price
        
        # Calculate new battery level
        energy_decrease = request.quantity
        percentage_decrease = (energy_decrease / capacity) * 100
        new_level = max(current_level - percentage_decrease, 0.0)  # Don't go below 0%
        
        # Update battery level
        update_success = update_battery_level(user_id, new_level)
        if not update_success:
            raise HTTPException(status_code=500, detail="Failed to update battery level")
        
        # Create a trade record
        total_revenue = request.quantity * price
        trade_data = {
            "User_ID": user_id,
            "type": "sell",
            "quantity": request.quantity,
            "price": price,
            "status": "executed",
            "execution_time": datetime.now(),
            "executed_at": datetime.now(),
            "created_at": datetime.now(),
            "resolution": 60,  # 1 hour resolution
            "market": "Electricity"
        }
        
        trade_created = create_trade(trade_data)
        if not trade_created:
            logger.error(f"Failed to create trade record for user {user_id}")
            # Continue anyway since the battery has been updated
        
        return {
            "success": True,
            "message": f"Successfully sold {request.quantity} kWh of electricity at {price} per kWh",
            "total_revenue": total_revenue,
            "new_battery_level": new_level,
            "trade_executed": datetime.now().isoformat()
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error selling electricity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Create a new trade
@router.post("/", response_model=Dict[str, Any])
async def create_trade_endpoint(
    trade_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    try:
        db = get_db()
        user_id = current_user.get("User_ID")
        
        # Validate portfolio belongs to user
        portfolio_id = trade_data.get("portfolio_id")
        if not portfolio_id:
            raise HTTPException(status_code=400, detail="Portfolio ID is required")
        
        portfolio_query = "SELECT * FROM portfolios WHERE portfolio_id = ? AND User_ID = ?"
        portfolio = db.execute_query(portfolio_query, (portfolio_id, user_id))
        
        if not portfolio:
            raise HTTPException(status_code=403, detail="Portfolio not found or doesn't belong to user")
        
        # Validate battery exists and belongs to portfolio
        battery_id = trade_data.get("battery_id")
        if battery_id:
            battery_query = "SELECT * FROM batteries WHERE battery_id = ? AND portfolio_id = ?"
            battery = db.execute_query(battery_query, (battery_id, portfolio_id))
            
            if not battery:
                raise HTTPException(status_code=404, detail="Battery not found or doesn't belong to portfolio")
        
        # Create trade with required fields
        new_trade = {
            "trade_id": str(uuid.uuid4()),
            "portfolio_id": portfolio_id,
            "battery_id": battery_id,
            "trade_type": trade_data.get("trade_type"),
            "energy_amount": trade_data.get("energy_amount"),
            "price": trade_data.get("price"),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "pending"
        }
        
        # Insert into database
        columns = ", ".join(new_trade.keys())
        placeholders = ", ".join(["?"] * len(new_trade))
        query = f"INSERT INTO trades ({columns}) VALUES ({placeholders})"
        
        db.execute_query(query, tuple(new_trade.values()))
        
        return {**new_trade, "message": "Trade created successfully"}
    except Exception as e:
        logger.error(f"Error creating trade: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating trade: {str(e)}")

# Get a specific trade by ID
@router.get("/{trade_id}", response_model=Dict[str, Any])
async def get_trade(
    trade_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    try:
        db = get_db()
        user_id = current_user.get("User_ID")
        
        # Query the trade ensuring it belongs to the user
        query = """
        SELECT t.* FROM trades t
        JOIN portfolios p ON t.portfolio_id = p.portfolio_id
        WHERE t.trade_id = ? AND p.User_ID = ?
        """
        
        trade = db.execute_query(query, (trade_id, user_id))
        
        if not trade or len(trade) == 0:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        return trade[0]
    except Exception as e:
        logger.error(f"Error retrieving trade: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving trade: {str(e)}")

# Update a trade (e.g., cancel it)
@router.patch("/{trade_id}", response_model=Dict[str, Any])
async def update_trade(
    trade_id: str,
    update_data: Dict[str, Any] = Body(...),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    try:
        db = get_db()
        user_id = current_user.get("User_ID")
        
        # Verify the trade exists and belongs to the user
        query = """
        SELECT t.* FROM trades t
        JOIN portfolios p ON t.portfolio_id = p.portfolio_id
        WHERE t.trade_id = ? AND p.User_ID = ?
        """
        
        trade = db.execute_query(query, (trade_id, user_id))
        
        if not trade or len(trade) == 0:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        # Only allow updating certain fields
        allowed_fields = ["status", "notes"]
        update_fields = {k: v for k, v in update_data.items() if k in allowed_fields}
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Build the update query
        set_clause = ", ".join([f"{field} = ?" for field in update_fields.keys()])
        update_query = f"UPDATE trades SET {set_clause} WHERE trade_id = ?"
        
        params = list(update_fields.values())
        params.append(trade_id)
        
        db.execute_query(update_query, tuple(params))
        
        # Return the updated trade
        updated_trade = db.execute_query("SELECT * FROM trades WHERE trade_id = ?", (trade_id,))
        
        if updated_trade and len(updated_trade) > 0:
            return {**updated_trade[0], "message": "Trade updated successfully"}
        else:
            return {"message": "Trade updated successfully"}
    except Exception as e:
        logger.error(f"Error updating trade: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating trade: {str(e)}") 