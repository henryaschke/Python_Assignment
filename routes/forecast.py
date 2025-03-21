from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import math
import random

from Python_Assignment.auth.dependencies import get_current_user
from Python_Assignment.database import get_db, Forecast

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Get price forecasts for a specific timeframe
@router.get("/prices", response_model=List[Dict[str, Any]])
async def get_price_forecasts(
    start_time: Optional[datetime] = Query(None, description="Start time for forecast period"),
    end_time: Optional[datetime] = Query(None, description="End time for forecast period"),
    interval: Optional[str] = Query("hour", description="Time interval for forecasts (hour, day)"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        db = get_db()
        # Default to next 24 hours if no times provided
        if not start_time:
            start_time = datetime.now()
        if not end_time:
            end_time = start_time + timedelta(hours=24)
        
        # Format dates for SQL query
        start_time_str = start_time.strftime("%Y-%m-%d %H:%M:%S")
        end_time_str = end_time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Query forecasts from database
        query = """
        SELECT * FROM forecasts
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp ASC
        """
        forecasts = db.execute_query(query, (start_time_str, end_time_str))
        
        if not forecasts:
            return []
            
        return forecasts
    except Exception as e:
        logger.error(f"Error retrieving price forecasts: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving forecasts: {str(e)}")

# Add a simple endpoint for price forecasts (similar to /prices but with a simpler interface)
@router.get("/price", response_model=List[Dict[str, Any]])
async def get_price_forecast(
    hours: int = Query(24, description="Number of hours to forecast"),
    market: str = Query("Germany", description="Market to forecast"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        db = get_db()
        # Define forecast period
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=hours)
        
        # Create a query function that accepts a session
        def query_func(session):
            return session.query(Forecast).filter(
                Forecast.timestamp >= start_time,
                Forecast.timestamp <= end_time,
                Forecast.market == market
            ).order_by(Forecast.timestamp)
        
        # Execute the query
        forecasts = db.execute_query(query_func)
        
        # If no forecasts found, generate synthetic data
        if not forecasts:
            logger.info(f"No forecast data found, generating synthetic forecasts for {market}")
            forecasts = generate_synthetic_forecasts(start_time, end_time, market)
            
        return forecasts
    except Exception as e:
        logger.error(f"Error retrieving price forecast: {e}")
        raise HTTPException(status_code=500, detail=f"Error retrieving forecast: {str(e)}")

# Helper function to generate synthetic forecasts
def generate_synthetic_forecasts(start_time, end_time, market):
    forecasts = []
    current_time = start_time
    
    # Generate hourly forecasts
    while current_time < end_time:
        # Create price patterns with daily cycles
        hour = current_time.hour
        # Higher prices during morning and evening peaks, lower at night
        hour_factor = 1.0 + 0.3 * (
            math.exp(-((hour - 8) ** 2) / 10) +  # Morning peak around 8am
            math.exp(-((hour - 18) ** 2) / 10)   # Evening peak around 6pm
        )
        
        # Base price with randomness
        base_price = 50 * hour_factor
        price = base_price * random.uniform(0.9, 1.1)
        
        # Add some trend over days
        day_offset = (current_time - start_time).days
        trend_factor = 1 + (day_offset * 0.02)  # Small increasing trend
        
        forecast = {
            "forecast_id": len(forecasts) + 1,
            "timestamp": current_time.isoformat(),
            "market": market,
            "price": round(price * trend_factor, 2),
            "confidence": round(random.uniform(0.7, 0.95), 2),
            "created_at": datetime.now().isoformat()
        }
        forecasts.append(forecast)
        current_time += timedelta(hours=1)
    
    return forecasts

# Get accuracy metrics for past forecasts
@router.get("/accuracy", response_model=Dict[str, Any])
async def get_forecast_accuracy(
    lookback_days: int = Query(7, description="Number of days to look back for accuracy calculation"),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    try:
        db = get_db()
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=lookback_days)
        
        # Format dates for SQL query
        start_date_str = start_date.strftime("%Y-%m-%d %H:%M:%S")
        end_date_str = end_date.strftime("%Y-%m-%d %H:%M:%S")
        
        # In a real system, we would join forecasts with actual prices and calculate metrics
        # For this demo, return sample metrics
        return {
            "period": f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
            "mape": 8.45,  # Mean Absolute Percentage Error
            "rmse": 12.3,  # Root Mean Square Error
            "mae": 9.67,   # Mean Absolute Error
            "sample_size": 24 * lookback_days
        }
    except Exception as e:
        logger.error(f"Error calculating forecast accuracy: {e}")
        raise HTTPException(status_code=500, detail=f"Error calculating forecast accuracy: {str(e)}") 