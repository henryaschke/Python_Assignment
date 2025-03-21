from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime, timedelta
import random
import math

from Python_Assignment.auth.dependencies import get_current_active_user
from Python_Assignment.database import get_market_data, get_market_data_today
from Python_Assignment.models.market import MarketDataPoint, MarketDataFilter

# Configure logging
logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

@router.get("/", response_model=List[Dict[str, Any]])
async def get_market_data_api(
    start_date: str = Query(None, description="Start date filter in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date filter in YYYY-MM-DD format"),
    min_price: float = Query(None, description="Minimum price filter"),
    max_price: float = Query(None, description="Maximum price filter"),
    market: str = Query("Germany", description="Market identifier"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """Get market data with optional filters."""
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Fetching market data for authenticated user_id: {user_id}")
        
        # Get data from database
        market_data = get_market_data(start_date, end_date, min_price, max_price, market)
        
        # If no data is found and it's for today, generate synthetic data
        if not market_data and (not start_date or start_date == datetime.now().strftime('%Y-%m-%d')):
            logger.info(f"No market data found for date range, generating synthetic data")
            market_data = generate_sample_market_data(
                start_date or datetime.now().strftime('%Y-%m-%d'), 
                market
            )
        
        return market_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/today", response_model=List[Dict[str, Any]])
async def get_market_data_today_api(
    delivery_period: int = Query(None, description="Hour of day (0-23)"),
    market: str = Query("Germany", description="Market identifier"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get today's market data for a given market, optionally filtered by delivery period.
    """
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Fetching today's market data for authenticated user_id: {user_id}")
        
        today = datetime.now().strftime('%Y-%m-%d')
        logger.info(f"Fetching market data for date: {today}, market: {market}")
        
        # Get data from database
        market_data = get_market_data_today(delivery_period)
        
        # If no data is found, generate synthetic data
        if not market_data:
            logger.info(f"No market data found for today, generating synthetic data")
            market_data = generate_sample_market_data(today, market)
            
            # Filter by delivery period if specified
            if delivery_period is not None:
                period_str = f"{delivery_period:02d}:00-{(delivery_period+1):02d}:00"
                market_data = [m for m in market_data if m.get("delivery_period") == period_str]
        
        return market_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting today's market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current", response_model=Dict[str, Any])
async def get_current_market_price(
    market: str = Query("Germany", description="Market identifier"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get the current market price (latest available price for the current hour).
    """
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Fetching current market price for authenticated user_id: {user_id}")
        
        # Get the current hour
        now = datetime.now()
        current_hour = now.hour
        today = now.strftime('%Y-%m-%d')
        
        # Get today's market data
        all_data = get_market_data_today(current_hour)
        
        # Filter for the current hour's data
        current_period = f"{current_hour:02d}:00-{(current_hour+1):02d}:00"
        current_data = [d for d in all_data if d.get("delivery_period") == current_period]
        
        # If no data found for current hour, generate it
        if not current_data:
            logger.info(f"No current market data found, generating synthetic data")
            all_generated_data = generate_sample_market_data(today, market)
            current_data = [d for d in all_generated_data if d.get("delivery_period") == current_period]
        
        # If we found data, return the first (and should be only) record
        if current_data:
            result = current_data[0]
            # Add a timestamp field for when this was retrieved
            result["timestamp"] = now.isoformat()
            return result
        
        # If still no data, create a simple response with estimated price
        base_price = 50 + 10 * math.sin(current_hour / 12 * math.pi)
        variation = random.uniform(-5, 5)
        current_price = round(base_price + variation, 2)
        
        return {
            "market": market,
            "price": current_price,
            "timestamp": now.isoformat(),
            "delivery_period": current_period,
            "status": "estimated"
        }
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting current market price: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_sample_market_data(date: str, market: str):
    """Generate synthetic market data for demo/testing purposes."""
    market_data = []
    
    # Convert date string to datetime
    try:
        date_obj = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        # Default to today if invalid date
        date_obj = datetime.now()
        date = date_obj.strftime('%Y-%m-%d')
    
    # Generate data for each hour of the day
    for hour in range(24):
        # Create random but somewhat realistic price patterns
        base_price = 50 + 10 * math.sin(hour / 12 * math.pi)
        variation = random.uniform(-5, 5)
        close_price = base_price + variation
        
        # Generate data point
        data_point = {
            "id": int(f"{date_obj.year}{date_obj.month:02d}{date_obj.day:02d}{hour:02d}"),
            "delivery_day": date,
            "delivery_period": f"{hour:02d}:00-{(hour+1):02d}:00",
            "cleared": hour < datetime.now().hour if date == datetime.now().strftime('%Y-%m-%d') else True,
            "market": market,
            "high": close_price + random.uniform(0, 3),
            "low": close_price - random.uniform(0, 3),
            "close": close_price,
            "open": close_price - random.uniform(-2, 2),
            "transaction_volume": random.uniform(100, 500),
            "created_at": datetime.now().isoformat()
        }
        market_data.append(data_point)
    
    return market_data

@router.get("/germany", response_model=List[Dict[str, Any]])
async def get_germany_market_data(
    start_date: str = Query(None, description="Start date in YYYY-MM-DD format"),
    end_date: str = Query(None, description="End date in YYYY-MM-DD format"),
    resolution: int = Query(None, description="Time resolution in minutes (15, 30, 60)"),
    limit: int = Query(1000, description="Maximum number of data points to return"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get historical market data for Germany with optional date range and resolution filters.
    """
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Fetching Germany market data for authenticated user_id: {user_id}")
        
        # Set default dates if not provided
        if not end_date:
            end_date = datetime.now().strftime('%Y-%m-%d')
        if not start_date:
            # Default to 7 days before end_date
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
            start_date = (end_date_obj - timedelta(days=7)).strftime('%Y-%m-%d')
        
        logger.info(f"Querying Germany market data from {start_date} to {end_date}, resolution: {resolution}")
        
        # In a real application, we would query historical market data from the database
        # For now, generate synthetic data
        market_data = generate_sample_germany_market_data(start_date, end_date, resolution)
        
        # Apply limit
        if len(market_data) > limit:
            market_data = market_data[:limit]
            
        return market_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting Germany market data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_sample_germany_market_data(start_date, end_date, resolution=None):
    """Generate synthetic historical market data for Germany."""
    market_data = []
    
    # Convert date strings to datetime
    try:
        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        # Default to recent dates if invalid
        end_date_obj = datetime.now()
        start_date_obj = end_date_obj - timedelta(days=7)
    
    # Use requested resolution or default to hourly (60 min)
    resolution = resolution or 60
    minutes_per_day = 24 * 60
    points_per_day = minutes_per_day // resolution
    
    # Generate data for each day in the range
    current_date = start_date_obj
    id_counter = 1
    
    while current_date <= end_date_obj:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Base price pattern with daily and weekly patterns
        day_of_week = current_date.weekday()  # 0-6 (Mon-Sun)
        weekend_factor = 1.0 - (0.2 if day_of_week >= 5 else 0)  # Lower prices on weekends
        
        for point_idx in range(points_per_day):
            # Time of day influences prices (higher during peak hours)
            hour_of_day = (point_idx * resolution) // 60
            minute_of_hour = (point_idx * resolution) % 60
            
            # Higher prices during morning and evening peaks
            time_factor = 1.0 + 0.3 * (
                math.exp(-((hour_of_day - 8) ** 2) / 10) +  # Morning peak around 8am
                math.exp(-((hour_of_day - 18) ** 2) / 10)    # Evening peak around 6pm
            )
            
            # Generate timestamp and period string
            timestamp = current_date.replace(
                hour=hour_of_day, 
                minute=minute_of_hour,
                second=0
            )
            
            period_end = timestamp + timedelta(minutes=resolution)
            period_str = f"{timestamp.strftime('%H:%M')}-{period_end.strftime('%H:%M')}"
            
            # Base price with some randomness
            base_price = 45 * weekend_factor * time_factor
            price_noise = random.uniform(0.9, 1.1)
            avg_price = base_price * price_noise
            
            # Create data point
            data_point = {
                "id": id_counter,
                "date": date_str,
                "resolution": f"{resolution}min",
                "delivery_period": period_str,
                "market": "Germany",
                "high_price": avg_price * random.uniform(1.01, 1.05),
                "low_price": avg_price * random.uniform(0.95, 0.99),
                "average_price": avg_price,
                "open_price": avg_price * random.uniform(0.98, 1.02),
                "close_price": avg_price * random.uniform(0.98, 1.02),
                "buy_volume": random.uniform(100, 300),
                "sell_volume": random.uniform(100, 300),
                "volume": random.uniform(200, 600),
                "vwap1h": avg_price * random.uniform(0.99, 1.01),
                "vwap3h": avg_price * random.uniform(0.98, 1.02),
                "contract_open_time": (timestamp - timedelta(hours=2)).isoformat(),
                "contract_close_time": (timestamp - timedelta(minutes=15)).isoformat(),
                "created_at": datetime.now().isoformat()
            }
            
            market_data.append(data_point)
            id_counter += 1
        
        current_date += timedelta(days=1)
    
    return market_data

@router.get("/realtime", response_model=Dict[str, Any])
async def get_realtime_prices(
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format (defaults to today)"),
    current_user: Dict[str, Any] = Depends(get_current_active_user)
):
    """
    Get real-time price data for today's trading.
    Returns current price and recent price history.
    """
    try:
        # Extract user_id from the current_user dictionary
        user_id = current_user.get("User_ID")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid user authentication")
            
        logger.info(f"Fetching real-time prices for authenticated user_id: {user_id}")
        
        # Use provided date or default to today
        date_str = date or datetime.now().strftime('%Y-%m-%d')
        
        # In a real application, we would query the latest price data
        # For demo purposes, generate synthetic data
        price_data = generate_sample_price_data(date_str)
        
        return price_data
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error getting real-time prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_sample_price_data(date_str: str):
    """Generate synthetic real-time price data for demo purposes."""
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        date_obj = datetime.now()
        date_str = date_obj.strftime('%Y-%m-%d')
    
    now = datetime.now()
    is_today = date_str == now.strftime('%Y-%m-%d')
    
    # For historical dates, use a fixed "current time" at end of day
    reference_time = now if is_today else date_obj.replace(hour=23, minute=0, second=0)
    
    # Current price with some randomness
    hour_of_day = reference_time.hour
    time_factor = 1.0 + 0.3 * (
        math.exp(-((hour_of_day - 8) ** 2) / 10) +  # Morning peak around 8am
        math.exp(-((hour_of_day - 18) ** 2) / 10)    # Evening peak around 6pm
    )
    
    current_price = 45 * time_factor * random.uniform(0.95, 1.05)
    
    # Generate price history for the day leading up to the reference time
    history = []
    
    # Generate points every 15 minutes up to the reference time
    start_time = date_obj.replace(hour=0, minute=0, second=0)
    current_time = start_time
    
    while current_time <= reference_time:
        hour = current_time.hour
        minute = current_time.minute
        
        # Price factors
        hour_factor = 1.0 + 0.3 * (
            math.exp(-((hour - 8) ** 2) / 10) +  # Morning peak around 8am
            math.exp(-((hour - 18) ** 2) / 10)    # Evening peak around 6pm
        )
        
        # Add some randomness and trends
        base_price = 45 * hour_factor
        noise = math.sin(minute / 60 * math.pi) * 1.5  # Sine wave within the hour
        random_factor = random.uniform(0.97, 1.03)
        
        price = base_price * random_factor + noise
        
        history.append({
            "timestamp": current_time.isoformat(),
            "price": price
        })
        
        current_time += timedelta(minutes=15)
    
    return {
        "date": date_str,
        "currentTime": reference_time.isoformat(),
        "currentPrice": current_price,
        "currency": "EUR",
        "unit": "MWh",
        "market": "Germany",
        "dayHigh": max(point["price"] for point in history),
        "dayLow": min(point["price"] for point in history),
        "dayAverage": sum(point["price"] for point in history) / len(history),
        "priceHistory": history
    } 