from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import random

from Python_Assignment.auth.dependencies import get_current_user, get_current_active_user
from Python_Assignment.database import get_db, get_user_trades

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# New endpoint to calculate trade profit/loss
@router.get("/trade-pnl", response_model=Dict[str, Any])
async def get_trade_profit_loss(
    start_date: Optional[str] = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: Optional[str] = Query(None, description="End date in YYYY-MM-DD format"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Calculate profit and loss from executed trades within a date range."""
    try:
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
        
        logger.info(f"Calculating trade P&L for user {user_id}")
        
        # Convert date strings to datetime objects if provided
        start_datetime = None
        end_datetime = None
        
        if start_date:
            try:
                start_datetime = datetime.fromisoformat(start_date)
            except ValueError:
                try:
                    start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Invalid start_date format: {start_date}")
                    raise HTTPException(status_code=400, detail="Invalid start_date format. Use YYYY-MM-DD")
        else:
            # Default to last 30 days if not specified
            start_datetime = datetime.now() - timedelta(days=30)
        
        if end_date:
            try:
                end_datetime = datetime.fromisoformat(end_date)
            except ValueError:
                try:
                    end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
                except ValueError:
                    logger.warning(f"Invalid end_date format: {end_date}")
                    raise HTTPException(status_code=400, detail="Invalid end_date format. Use YYYY-MM-DD")
        else:
            # Default to current date if not specified
            end_datetime = datetime.now()
        
        # Get user trades within the specified time period
        trades = get_user_trades(user_id, start_datetime, end_datetime)
        
        # Calculate P&L metrics
        buy_volume = 0
        buy_cost = 0
        sell_volume = 0
        sell_revenue = 0
        total_trades = len(trades)
        executed_trades = 0
        
        for trade in trades:
            if trade.get("status") != "executed":
                continue
                
            executed_trades += 1
            trade_type = trade.get("type", "").lower()
            quantity = trade.get("quantity", 0)
            price = trade.get("price", 0)
            
            if trade_type == "buy":
                buy_volume += quantity
                buy_cost += quantity * price
            elif trade_type == "sell":
                sell_volume += quantity
                sell_revenue += quantity * price
        
        # Calculate overall P&L
        net_volume = buy_volume - sell_volume
        net_cost = buy_cost - sell_revenue
        
        # Average prices
        avg_buy_price = buy_cost / buy_volume if buy_volume > 0 else 0
        avg_sell_price = sell_revenue / sell_volume if sell_volume > 0 else 0
        
        # Profit/Loss calculation
        profit_loss = sell_revenue - buy_cost
        profit_loss_per_kWh = profit_loss / (buy_volume + sell_volume) if (buy_volume + sell_volume) > 0 else 0
        
        return {
            "period": {
                "start_date": start_datetime.strftime("%Y-%m-%d"),
                "end_date": end_datetime.strftime("%Y-%m-%d")
            },
            "trades": {
                "total": total_trades,
                "executed": executed_trades
            },
            "volume": {
                "buy": buy_volume,
                "sell": sell_volume,
                "net": net_volume  # Positive means net buy, negative means net sell
            },
            "financials": {
                "buy_cost": round(buy_cost, 2),
                "sell_revenue": round(sell_revenue, 2),
                "net_cost": round(net_cost, 2),  # Positive means net cost, negative means net revenue
                "avg_buy_price": round(avg_buy_price, 2),
                "avg_sell_price": round(avg_sell_price, 2),
                "profit_loss": round(profit_loss, 2),
                "profit_loss_per_kWh": round(profit_loss_per_kWh, 2)
            }
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error calculating trade P&L: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating profit/loss metrics: {str(e)}")

# Get portfolio performance metrics
@router.get("/portfolio", response_model=Dict[str, Any])
async def get_portfolio_performance(
    portfolio_id: Optional[int] = Query(None, description="Portfolio ID to get metrics for"),
    timeframe: str = Query("month", description="Timeframe for metrics (day, week, month, year)"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    try:
        db = get_db()
        user_id = current_user.get("User_ID")
        
        # Calculate date range based on timeframe
        end_date = datetime.now()
        if timeframe == "day":
            start_date = end_date - timedelta(days=1)
        elif timeframe == "week":
            start_date = end_date - timedelta(weeks=1)
        elif timeframe == "year":
            start_date = end_date - timedelta(days=365)
        else:  # default to month
            start_date = end_date - timedelta(days=30)
        
        # In a real implementation, we would calculate these metrics from trade data
        # For demo, return sample metrics regardless of whether portfolios are found
        return {
            "portfolio_id": portfolio_id or 1,  # Default to 1 if not provided
            "timeframe": timeframe,
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "metrics": {
                "total_trades": 42,
                "profit_loss": 2850.75,
                "profit_loss_percent": 12.45,
                "successful_trades": 28,
                "success_rate": 66.7,
                "avg_trade_duration": 4.2  # hours
            }
        }
    except Exception as e:
        logger.error(f"Error retrieving portfolio performance: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving performance metrics: {str(e)}")

# Get battery utilization metrics
@router.get("/battery-utilization", response_model=Dict[str, Any])
async def get_battery_utilization(
    battery_id: Optional[int] = Query(None, description="Battery ID to get metrics for"),
    timeframe: str = Query("week", description="Timeframe for metrics (day, week, month)"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    try:
        user_id = current_user.get("User_ID")
        
        # Calculate metrics - in real implementation these would come from actual data
        # For demo, return sample data regardless of whether batteries are found
        utilization_data = {
            "battery_id": battery_id or 1,  # Default to 1 if not provided
            "timeframe": timeframe,
            "capacity_utilization": 78.5,  # percentage
            "charge_cycles": 24,
            "avg_charge_time": 2.4,  # hours
            "avg_discharge_time": 3.2,  # hours
            "efficiency": 92.8,  # percentage
            "revenue_generated": 342.50,
            "cost_savings": 185.75
        }
        
        return utilization_data
    except Exception as e:
        logger.error(f"Error retrieving battery utilization: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving battery metrics: {str(e)}") 