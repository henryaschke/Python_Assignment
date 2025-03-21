import logging
import random
import math
from datetime import datetime, timedelta
from passlib.context import CryptContext
from database import (
    get_db, User, Portfolio, Battery, Trade, MarketData, HistoricalMarketData, Forecast
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_test_users():
    """Create test users in the database."""
    db = get_db()
    
    # Check if users already exist
    def check_users(session):
        return session.query(User).count()
    
    user_count = db.execute_query(check_users)[0]["result"]
    if user_count > 0:
        logger.info(f"Database already has {user_count} users, skipping user creation")
        return
    
    # Create test users
    test_users = [
        {
            "email": "admin@example.com",
            "hashed_password": pwd_context.hash("admin123"),
            "name": "Admin User",
            "created_at": datetime.now(),
            "is_active": True
        },
        {
            "email": "user@example.com",
            "hashed_password": pwd_context.hash("user123"),
            "name": "Test User",
            "created_at": datetime.now(),
            "is_active": True
        },
        {
            "email": "trader@example.com",
            "hashed_password": pwd_context.hash("trader123"),
            "name": "Energy Trader",
            "created_at": datetime.now(),
            "is_active": True
        }
    ]
    
    for user_data in test_users:
        db.insert_row(User, user_data)
        logger.info(f"Created test user: {user_data['email']}")

def create_portfolios_and_batteries():
    """Create portfolios and batteries for existing users."""
    db = get_db()
    
    # Get all users
    def get_users(session):
        return session.query(User).all()
    
    users_result = db.execute_query(get_users)
    
    for user in users_result:
        # Fix: Access the correct key for the user ID
        # In SQLAlchemy results, the column names match the model's column names
        user_id = user.get("User_ID")
        
        # If User_ID key doesn't exist, try lowercase variant
        if user_id is None:
            user_id = user.get("user_id")
            
        # If still not found, look for any ID-like field
        if user_id is None:
            for key in user:
                if "id" in key.lower():
                    user_id = user[key]
                    logger.info(f"Found user ID in field {key}: {user_id}")
                    break
        
        if not user_id:
            logger.error(f"Could not determine user ID from user object: {user}")
            continue
        
        # Create portfolio if not exists
        def check_portfolio(session):
            return session.query(Portfolio).filter(Portfolio.User_ID == user_id).count()
        
        portfolio_count = db.execute_query(check_portfolio)[0]["result"]
        if portfolio_count == 0:
            portfolio_data = {
                "User_ID": user_id,
                "balance": 10000.0 + random.uniform(-2000, 2000),
                "profit_loss": random.uniform(-500, 1500),
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            db.insert_row(Portfolio, portfolio_data)
            logger.info(f"Created portfolio for user {user_id}")
        
        # Create battery if not exists
        def check_battery(session):
            return session.query(Battery).filter(Battery.User_ID == user_id).count()
        
        battery_count = db.execute_query(check_battery)[0]["result"]
        if battery_count == 0:
            battery_data = {
                "User_ID": user_id,
                "current_level": random.uniform(30, 80),
                "capacity": random.choice([50.0, 100.0, 150.0]),
                "max_charge_rate": 10.0,
                "max_discharge_rate": 10.0,
                "efficiency": 0.95,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            db.insert_row(Battery, battery_data)
            logger.info(f"Created battery for user {user_id}")

def create_sample_trades():
    """Create sample trades for each user."""
    db = get_db()
    
    # Get all users
    def get_users(session):
        return session.query(User).all()
    
    users_result = db.execute_query(get_users)
    
    # Create trades for each user
    for user in users_result:
        # Fix: Access the correct key for the user ID
        user_id = user.get("User_ID")
        
        # If User_ID key doesn't exist, try lowercase variant
        if user_id is None:
            user_id = user.get("user_id")
            
        # If still not found, look for any ID-like field
        if user_id is None:
            for key in user:
                if "id" in key.lower():
                    user_id = user[key]
                    break
        
        if not user_id:
            logger.error(f"Could not determine user ID from user object: {user}")
            continue
        
        # Check if user already has trades
        def check_trades(session):
            return session.query(Trade).filter(Trade.User_ID == user_id).count()
        
        trade_count = db.execute_query(check_trades)[0]["result"]
        if trade_count > 0:
            logger.info(f"User {user_id} already has {trade_count} trades, skipping")
            continue
        
        # Create 10-20 random trades over the past 7 days
        num_trades = random.randint(10, 20)
        now = datetime.now()
        
        for i in range(num_trades):
            # Random trade properties
            trade_type = random.choice(["buy", "sell"])
            quantity = random.uniform(1, 10)
            price = random.uniform(30, 70)
            status = random.choice(["executed", "executed", "executed", "pending", "cancelled"])
            
            # Random times over past week
            hours_ago = random.randint(0, 24 * 7)
            minutes_ago = random.randint(0, 59)
            execution_time = now - timedelta(hours=hours_ago, minutes=minutes_ago)
            
            # For executed trades, set executed_at
            executed_at = execution_time + timedelta(minutes=random.randint(1, 30)) if status == "executed" else None
            
            # Create trade
            trade_data = {
                "User_ID": user_id,
                "type": trade_type,
                "quantity": quantity,
                "price": price if status == "executed" else None,
                "status": status,
                "execution_time": execution_time,
                "executed_at": executed_at,
                "created_at": execution_time - timedelta(minutes=random.randint(10, 60)),
                "resolution": random.choice([15, 30, 60]),
                "market": "Germany"
            }
            
            db.insert_row(Trade, trade_data)
        
        logger.info(f"Created {num_trades} sample trades for user {user_id}")

def create_market_data():
    """Create sample market data for the past 30 days."""
    db = get_db()
    
    # Check if market data already exists
    def check_market_data(session):
        return session.query(MarketData).count()
    
    data_count = db.execute_query(check_market_data)[0]["result"]
    if data_count > 0:
        logger.info(f"Database already has {data_count} market data points, skipping")
        return
    
    # Generate market data for the past 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        
        # Generate hourly data for each day
        for hour in range(24):
            # Skip future hours for today
            if current_date.date() == end_date.date() and hour > end_date.hour:
                continue
            
            # Create random but somewhat realistic price patterns
            base_price = 50 + 10 * math.sin(hour / 12 * math.pi)
            variation = random.uniform(-5, 5)
            close_price = base_price + variation
            
            # Create market data entry
            data_point = {
                "delivery_day": date_str,
                "delivery_period": f"{hour:02d}:00-{(hour+1):02d}:00",
                "cleared": True,
                "market": "Germany",
                "high": close_price + random.uniform(0, 3),
                "low": close_price - random.uniform(0, 3),
                "close": close_price,
                "open": close_price - random.uniform(-2, 2),
                "transaction_volume": random.uniform(100, 500),
                "created_at": datetime.now()
            }
            
            db.insert_row(MarketData, data_point)
        
        current_date += timedelta(days=1)
    
    logger.info(f"Created market data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")

def create_forecasts():
    """Create sample price forecasts for the next week."""
    db = get_db()
    
    # Check if forecasts already exist
    def check_forecasts(session):
        return session.query(Forecast).count()
    
    forecast_count = db.execute_query(check_forecasts)[0]["result"]
    if forecast_count > 0:
        logger.info(f"Database already has {forecast_count} forecasts, skipping")
        return
    
    # Generate hourly forecasts for the next 7 days
    start_timestamp = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    end_timestamp = start_timestamp + timedelta(days=7)
    
    current_timestamp = start_timestamp
    while current_timestamp < end_timestamp:
        hour = current_timestamp.hour
        
        # Base price with hourly pattern
        base_price = 50 + 10 * math.sin(hour / 12 * math.pi)
        confidence = random.uniform(0.7, 0.95)
        
        # Add some randomness
        predicted_price = base_price + random.uniform(-3, 3)
        uncertainty = predicted_price * (1 - confidence)
        
        # Create forecast entry
        forecast_data = {
            "timestamp": current_timestamp,
            "market": "Germany",
            "predicted_price": predicted_price,
            "lower_bound": predicted_price - uncertainty,
            "upper_bound": predicted_price + uncertainty,
            "confidence": confidence,
            "created_at": datetime.now()
        }
        
        db.insert_row(Forecast, forecast_data)
        current_timestamp += timedelta(hours=1)
    
    logger.info(f"Created forecasts from {start_timestamp} to {end_timestamp}")

def seed_database():
    """Seed the database with sample data."""
    logger.info("Starting database seeding...")
    
    # Initialize database and create tables
    db = get_db()
    
    # Create seed data
    create_test_users()
    create_portfolios_and_batteries()
    create_sample_trades()
    create_market_data()
    create_forecasts()
    
    logger.info("Database seeding completed!")

if __name__ == "__main__":
    seed_database() 