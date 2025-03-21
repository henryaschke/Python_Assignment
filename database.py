from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, ForeignKey, func, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import logging
import os
import json
import math
import random

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database file location
DATABASE_URL = "sqlite:///./energy_trading.db"

# Create SQLAlchemy Base
Base = declarative_base()

# Define SQLAlchemy Models
class User(Base):
    __tablename__ = "users"

    User_ID = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="user", uselist=False)
    battery = relationship("Battery", back_populates="user", uselist=False)
    trades = relationship("Trade", back_populates="user")


class Portfolio(Base):
    __tablename__ = "portfolios"

    Portfolio_ID = Column(Integer, primary_key=True, autoincrement=True)
    User_ID = Column(Integer, ForeignKey("users.User_ID"), nullable=False)
    balance = Column(Float, default=10000.0)  # Default starting balance
    profit_loss = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="portfolio")


class Battery(Base):
    __tablename__ = "batteries"

    Battery_ID = Column(Integer, primary_key=True, autoincrement=True)
    User_ID = Column(Integer, ForeignKey("users.User_ID"), nullable=False)
    current_level = Column(Float, default=50.0)  # Battery level percentage
    capacity = Column(Float, default=100.0)  # Capacity in kWh
    max_charge_rate = Column(Float, default=10.0)  # Max charge rate in kW
    max_discharge_rate = Column(Float, default=10.0)  # Max discharge rate in kW
    efficiency = Column(Float, default=0.95)  # Battery efficiency 
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Relationships
    user = relationship("User", back_populates="battery")


class Trade(Base):
    __tablename__ = "trades"

    Trade_ID = Column(Integer, primary_key=True, autoincrement=True)
    User_ID = Column(Integer, ForeignKey("users.User_ID"), nullable=False)
    type = Column(String, nullable=False)  # 'buy' or 'sell'
    quantity = Column(Float, nullable=False)
    price = Column(Float)
    status = Column(String, default="pending")  # pending, executed, cancelled
    execution_time = Column(DateTime)
    executed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    resolution = Column(Integer)  # Market resolution in minutes (15, 30, or 60)
    market = Column(String, default="Germany")
    
    # Relationships
    user = relationship("User", back_populates="trades")


class MarketData(Base):
    __tablename__ = "market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    delivery_day = Column(String, nullable=False)
    delivery_period = Column(String, nullable=False)
    cleared = Column(Boolean, default=False)
    market = Column(String, default="Germany")
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    open = Column(Float)
    transaction_volume = Column(Float)
    created_at = Column(DateTime, default=datetime.now)


class HistoricalMarketData(Base):
    __tablename__ = "historical_market_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)
    resolution = Column(String, nullable=False)
    delivery_period = Column(String, nullable=False)
    market = Column(String, default="Germany")
    high_price = Column(Float)
    low_price = Column(Float)
    average_price = Column(Float)
    open_price = Column(Float)
    close_price = Column(Float)
    buy_volume = Column(Float)
    sell_volume = Column(Float)
    volume = Column(Float)
    vwap3h = Column(Float)
    vwap1h = Column(Float)
    contract_open_time = Column(String)
    contract_close_time = Column(String)
    created_at = Column(DateTime, default=datetime.now)


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    market = Column(String, default="Germany")
    predicted_price = Column(Float, nullable=False)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    confidence = Column(Float)
    created_at = Column(DateTime, default=datetime.now)

# Cache for user trades to avoid repeated DB calls
_user_trades_cache = {}
_user_trades_cache_ttl = 300  # 5 minutes TTL
_user_trades_cache_last_updated = {}

# Global database instance for singleton pattern
_db_instance = None

class SQLAlchemyDatabase:
    def __init__(self):
        """
        Initializes a SQLAlchemy engine and session
        """
        self.engine = None
        self.Session = None
        try:
            self.engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
            self.Session = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            logger.info("SQLAlchemy engine initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing SQLAlchemy engine: {e}")
            raise
    
    def create_tables(self):
        """Create all tables in the database"""
        try:
            Base.metadata.create_all(self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def execute_query(self, query_func, timeout: int = 60) -> List[Dict[str, Any]]:
        """
        Execute a SQLAlchemy query function and return the results as a list of dictionaries.
        The query_func should accept a session parameter and return a query result.
        """
        try:
            logger.info(f"Executing SQLAlchemy query with timeout={timeout}s")
            
            with self.Session() as session:
                start_time = datetime.now()
                result = query_func(session)
                query_time = (datetime.now() - start_time).total_seconds()
                logger.info(f"Query executed in {query_time:.2f} seconds")
                
                # Convert results to a list of dicts
                if hasattr(result, 'all'):
                    # This is a SQLAlchemy query result that can be iterated
                    rows = result.all()
                    result_list = []
                    for row in rows:
                        row_dict = {}
                        if hasattr(row, '_asdict'):  # For SQLAlchemy Row objects
                            row_dict = row._asdict()
                        elif hasattr(row, '__table__'):  # For SQLAlchemy ORM models
                            for column in row.__table__.columns:
                                # Use column.key to get the Python attribute name
                                value = getattr(row, column.key, None)
                                # Use column.name for the dict key (DB column name)
                                row_dict[column.name] = value
                        elif isinstance(row, dict):  # Already a dict
                            row_dict = row
                        else:  # Fallback for other types
                            try:
                                row_dict = dict(row)
                            except (TypeError, ValueError):
                                # Last resort: try to convert using __dict__
                                if hasattr(row, '__dict__'):
                                    row_dict = row.__dict__
                                    # Remove SQLAlchemy internal attributes
                                    if '_sa_instance_state' in row_dict:
                                        del row_dict['_sa_instance_state']
                        
                        # Convert datetime objects to ISO format strings
                        for key, value in row_dict.items():
                            if isinstance(value, datetime):
                                row_dict[key] = value.isoformat()
                        
                        # Make sure primary keys use consistent naming (both ID and _id forms)
                        for key in list(row_dict.keys()):
                            if key.endswith('_ID') and key[:-3].lower() + '_id' not in row_dict:
                                row_dict[key[:-3].lower() + '_id'] = row_dict[key]
                            elif key.endswith('_id') and key[:-3].upper() + '_ID' not in row_dict:
                                row_dict[key[:-3].upper() + '_ID'] = row_dict[key]
                        
                        result_list.append(row_dict)
                    
                    logger.info(f"Query returned {len(result_list)} rows")
                    return result_list
                elif result is None:
                    return []
                elif hasattr(result, '__table__'):  # Single SQLAlchemy ORM model
                    # Convert the single ORM model to a dictionary
                    row_dict = {}
                    for column in result.__table__.columns:
                        value = getattr(result, column.key, None)
                        row_dict[column.name] = value
                        
                        # Also add lowercase version of ID fields for consistency
                        if column.name.endswith('_ID'):
                            row_dict[column.name[:-3].lower() + '_id'] = value
                    
                    # Convert datetime objects to ISO format strings
                    for key, value in row_dict.items():
                        if isinstance(value, datetime):
                            row_dict[key] = value.isoformat()
                    
                    return [row_dict]
                else:
                    # For non-query results (like count)
                    return [{"result": result}]
                
        except Exception as e:
            error_type = type(e).__name__
            logger.error(f"Query execution error ({error_type}): {str(e)}")
            # Return empty list on error rather than raising
            logger.warning("Returning empty list due to query error")
            return []
    
    def insert_row(self, model_class, row_data: Dict[str, Any]) -> bool:
        """Insert a single row into a table."""
        try:
            with self.Session() as session, session.begin():
                # Create a new model instance with the provided data
                new_record = model_class(**row_data)
                session.add(new_record)
                session.commit()
                logger.info(f"Inserted row into {model_class.__tablename__}")
                return True
        except Exception as e:
            logger.error(f"Error inserting row into {model_class.__tablename__}: {str(e)}")
            return False

    def update_row(
        self, 
        model_class, 
        update_data: Dict[str, Any], 
        condition_field: str, 
        condition_value: Any
    ) -> bool:
        """Update a row in a table based on a condition."""
        try:
            with self.Session() as session, session.begin():
                # Find the record to update
                record = session.query(model_class).filter(
                    getattr(model_class, condition_field) == condition_value
                ).first()
                
                if not record:
                    logger.warning(f"No record found to update in {model_class.__tablename__} where {condition_field}={condition_value}")
                    return False
                
                # Update the record with the provided data
                for key, value in update_data.items():
                    setattr(record, key, value)
                
                session.commit()
                logger.info(f"Updated row in {model_class.__tablename__} where {condition_field}={condition_value}")
                return True
        except Exception as e:
            logger.error(f"Error updating row in {model_class.__tablename__}: {str(e)}")
            return False

    def delete_row(
        self, 
        model_class, 
        condition_field: str, 
        condition_value: Any
    ) -> bool:
        """Delete a row from a table based on a condition."""
        try:
            with self.Session() as session, session.begin():
                # Find and delete the record
                record = session.query(model_class).filter(
                    getattr(model_class, condition_field) == condition_value
                ).first()
                
                if not record:
                    logger.warning(f"No record found to delete in {model_class.__tablename__} where {condition_field}={condition_value}")
                    return False
                
                session.delete(record)
                session.commit()
                logger.info(f"Deleted row from {model_class.__tablename__} where {condition_field}={condition_value}")
                return True
        except Exception as e:
            logger.error(f"Error deleting row from {model_class.__tablename__}: {str(e)}")
            return False

def get_db() -> SQLAlchemyDatabase:
    """
    Returns a singleton instance of the SQLAlchemyDatabase.
    Creates it if it doesn't exist yet.
    """
    global _db_instance
    if _db_instance is None:
        _db_instance = SQLAlchemyDatabase()
        _db_instance.create_tables()
    return _db_instance

def get_session() -> Session:
    """
    Returns a new SQLAlchemy session.
    """
    db = get_db()
    return db.Session()

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get a user by email."""
    db = get_db()
    def query_func(session):
        return session.query(User).filter(User.email == email).first()
    
    results = db.execute_query(query_func)
    # When the result is a single object (which should be for this query)
    # it's wrapped in a {'result': <user_object>} dict
    if results and len(results) == 1 and 'result' in results[0]:
        # The SQLAlchemy object is in the 'result' key
        user_obj = results[0]['result']
        
        # Check if it's an SQLAlchemy model object
        if hasattr(user_obj, '__table__'):
            # Convert to dict manually
            user_dict = {}
            for column in user_obj.__table__.columns:
                user_dict[column.name] = getattr(user_obj, column.key, None)
            return user_dict
        
        # If it's already a dict, return it
        if isinstance(user_obj, dict):
            return user_obj
            
    # If the result is already properly formatted, return the first item
    return results[0] if results else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get a user by ID."""
    db = get_db()
    def query_func(session):
        return session.query(User).filter(User.User_ID == user_id).first()
    
    results = db.execute_query(query_func)
    # When the result is a single object (which should be for this query)
    # it's wrapped in a {'result': <user_object>} dict
    if results and len(results) == 1 and 'result' in results[0]:
        # The SQLAlchemy object is in the 'result' key
        user_obj = results[0]['result']
        
        # Check if it's an SQLAlchemy model object
        if hasattr(user_obj, '__table__'):
            # Convert to dict manually
            user_dict = {}
            for column in user_obj.__table__.columns:
                user_dict[column.name] = getattr(user_obj, column.key, None)
            return user_dict
        
        # If it's already a dict, return it
        if isinstance(user_obj, dict):
            return user_obj
            
    # If the result is already properly formatted, return the first item
    return results[0] if results else None

def get_portfolio_by_user_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get a user's portfolio by their user ID."""
    db = get_db()
    def query_func(session):
        return session.query(Portfolio).filter(Portfolio.User_ID == user_id).first()
    
    results = db.execute_query(query_func)
    return results[0] if results else None

def get_user_trades(
    user_id: int, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None,
    cache_bypass: bool = False
) -> List[Dict[str, Any]]:
    """Get trades for a user, with optional date filtering."""
    # Check cache first, unless bypass is requested
    cache_key = f"user_{user_id}_trades"
    current_time = datetime.now()
    
    if not cache_bypass and cache_key in _user_trades_cache:
        last_updated = _user_trades_cache_last_updated.get(cache_key, datetime.min)
        if (current_time - last_updated).total_seconds() < _user_trades_cache_ttl:
            cached_trades = _user_trades_cache[cache_key]
            logger.info(f"Returning {len(cached_trades)} cached trades for user {user_id}")
            
            # Apply date filtering on the cached data if needed
            if start_date or end_date:
                filtered_trades = []
                for trade in cached_trades:
                    trade_date = datetime.fromisoformat(trade['execution_time']) if isinstance(trade['execution_time'], str) else trade['execution_time']
                    if start_date and trade_date < start_date:
                        continue
                    if end_date and trade_date > end_date:
                        continue
                    filtered_trades.append(trade)
                return filtered_trades
            
            return cached_trades
    
    # If not in cache or cache bypassed, query database
    db = get_db()
    
    def query_func(session):
        query = session.query(Trade).filter(Trade.User_ID == user_id)
        
        if start_date:
            query = query.filter(Trade.execution_time >= start_date)
        if end_date:
            query = query.filter(Trade.execution_time <= end_date)
            
        return query.order_by(Trade.execution_time.desc())
    
    trades = db.execute_query(query_func)
    
    # Update cache
    if not start_date and not end_date:
        _user_trades_cache[cache_key] = trades
        _user_trades_cache_last_updated[cache_key] = current_time
        logger.info(f"Updated cache with {len(trades)} trades for user {user_id}")
    
    return trades

def create_trade(trade_data: Dict[str, Any]) -> bool:
    """Create a new trade record."""
    db = get_db()
    
    # Make sure we have a User_ID
    if "User_ID" not in trade_data or not trade_data["User_ID"]:
        logger.error("Cannot create trade without User_ID")
        return False
    
    # Convert execution_time string to datetime if needed
    if "execution_time" in trade_data and isinstance(trade_data["execution_time"], str):
        try:
            trade_data["execution_time"] = datetime.fromisoformat(trade_data["execution_time"].replace('Z', '+00:00'))
        except ValueError:
            logger.error(f"Invalid execution_time format: {trade_data['execution_time']}")
            return False
    
    # Insert the trade
    return db.insert_row(Trade, trade_data)

def get_market_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    market: str = "Germany"
) -> List[Dict[str, Any]]:
    """Get market data with optional filtering by date and price range."""
    db = get_db()
    
    def query_func(session):
        query = session.query(MarketData).filter(MarketData.market == market)
        
        if start_date:
            query = query.filter(MarketData.delivery_day >= start_date)
        if end_date:
            query = query.filter(MarketData.delivery_day <= end_date)
        if min_price is not None:
            query = query.filter(MarketData.close >= min_price)
        if max_price is not None:
            query = query.filter(MarketData.close <= max_price)
            
        return query.order_by(MarketData.delivery_day, MarketData.delivery_period)
    
    return db.execute_query(query_func)

def get_forecasts(
    market: str = "Germany",
    start_timestamp: Optional[datetime] = None,
    end_timestamp: Optional[datetime] = None
) -> List[Dict[str, Any]]:
    """Get price forecasts for a specific market and time range."""
    db = get_db()
    
    def query_func(session):
        query = session.query(Forecast).filter(Forecast.market == market)
        
        if start_timestamp:
            query = query.filter(Forecast.timestamp >= start_timestamp)
        if end_timestamp:
            query = query.filter(Forecast.timestamp <= end_timestamp)
            
        return query.order_by(Forecast.timestamp)
    
    return db.execute_query(query_func)

def get_battery_status(user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Get a user's battery status."""
    db = get_db()
    
    def query_func(session):
        if user_id:
            return session.query(Battery).filter(Battery.User_ID == user_id).first()
        else:
            return session.query(Battery).first()  # Return any battery if no specific user
    
    results = db.execute_query(query_func)
    if not results:
        return None
    
    battery_data = results[0]
    
    # Calculate additional fields
    capacity = battery_data.get('capacity', 100.0)
    current_level = battery_data.get('current_level', 50.0)
    
    # Add derived fields
    battery_data['current_energy'] = (current_level / 100.0) * capacity
    battery_data['remaining_capacity'] = capacity - battery_data['current_energy']
    
    return battery_data

def get_performance_metrics(
    user_id: int, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """Get performance metrics for a user over a time period."""
    db = get_db()
    
    # Get the user's portfolio
    def portfolio_query(session):
        return session.query(Portfolio).filter(Portfolio.User_ID == user_id).first()
    
    portfolio_results = db.execute_query(portfolio_query)
    if not portfolio_results:
        return {"error": "Portfolio not found"}
    
    portfolio = portfolio_results[0]
    
    # Get the user's trades in the specified period
    trades = get_user_trades(user_id, start_date, end_date, cache_bypass=True)
    
    # Calculate metrics
    metrics = {
        "user_id": user_id,
        "balance": portfolio.get('balance', 0),
        "profit_loss": portfolio.get('profit_loss', 0),
        "trade_count": len(trades),
        "buy_trades": sum(1 for t in trades if t.get('type') == 'buy'),
        "sell_trades": sum(1 for t in trades if t.get('type') == 'sell'),
        "executed_trades": sum(1 for t in trades if t.get('status') == 'executed'),
        "pending_trades": sum(1 for t in trades if t.get('status') == 'pending'),
        "cancelled_trades": sum(1 for t in trades if t.get('status') == 'cancelled'),
    }
    
    # Add time period info
    if start_date:
        metrics["start_date"] = start_date.isoformat()
    if end_date:
        metrics["end_date"] = end_date.isoformat()
    
    return metrics

def test_db_connection() -> bool:
    """Test the database connection."""
    try:
        db = get_db()
        with db.Session() as session:
            session.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

def create_battery_if_not_exists(user_id: Optional[int] = None) -> Dict[str, Any]:
    """Create a battery for a user if one doesn't already exist."""
    if not user_id:
        logger.error("Cannot create battery without user_id")
        return {"error": "User ID required"}
    
    db = get_db()
    
    # Check if battery already exists
    def check_query(session):
        return session.query(Battery).filter(Battery.User_ID == user_id).first()
    
    existing_battery = db.execute_query(check_query)
    
    if existing_battery:
        logger.info(f"Battery already exists for user {user_id}")
        return existing_battery[0]
    
    # Create new battery
    battery_data = {
        "User_ID": user_id,
        "current_level": 50.0,
        "capacity": 100.0,
        "max_charge_rate": 10.0,
        "max_discharge_rate": 10.0,
        "efficiency": 0.95,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    success = db.insert_row(Battery, battery_data)
    
    if success:
        logger.info(f"Created new battery for user {user_id}")
        # Get the newly created battery
        new_battery = db.execute_query(check_query)
        return new_battery[0] if new_battery else {"error": "Failed to retrieve new battery"}
    else:
        return {"error": "Failed to create battery"}

def get_pending_trades() -> List[Dict[str, Any]]:
    """Get all pending trades."""
    db = get_db()
    
    def query_func(session):
        return session.query(Trade).filter(
            Trade.status == "pending",
            Trade.execution_time <= datetime.now()
        ).order_by(Trade.execution_time)
    
    return db.execute_query(query_func)

def get_trade_by_id(trade_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Get a trade by its ID, optionally filtering by user ID."""
    db = get_db()
    
    def query_func(session):
        query = session.query(Trade).filter(Trade.Trade_ID == trade_id)
        if user_id:
            query = query.filter(Trade.User_ID == user_id)
        return query.first()
    
    results = db.execute_query(query_func)
    return results[0] if results else None

def update_trade_status(trade_id: int, update_data: Dict[str, Any]) -> bool:
    """Update a trade's status and related fields."""
    db = get_db()
    
    # Get the existing trade
    trade = get_trade_by_id(trade_id)
    if not trade:
        logger.error(f"Trade {trade_id} not found for status update")
        return False
    
    # Update the trade
    return db.update_row(Trade, update_data, "Trade_ID", trade_id)

def update_battery_level(user_id: int, new_level: float) -> bool:
    """Update a user's battery level."""
    db = get_db()
    
    # Get the existing battery
    def battery_query(session):
        return session.query(Battery).filter(Battery.User_ID == user_id).first()
    
    battery_results = db.execute_query(battery_query)
    if not battery_results:
        logger.error(f"Battery for user {user_id} not found")
        return False
    
    # Update the battery
    update_data = {
        "current_level": new_level,
        "updated_at": datetime.now()
    }
    
    return db.update_row(Battery, update_data, "User_ID", user_id)

def get_market_data_today(delivery_period: int = None, resolution: int = None) -> List[Dict[str, Any]]:
    """Get market data for today."""
    db = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    
    def query_func(session):
        query = session.query(MarketData).filter(MarketData.delivery_day == today)
        
        if delivery_period:
            # Convert delivery_period (hour) to delivery_period string format
            period_str = f"{delivery_period:02d}:00-{(delivery_period+1):02d}:00"
            query = query.filter(MarketData.delivery_period == period_str)
            
        return query.order_by(MarketData.delivery_period)
    
    return db.execute_query(query_func)

def update_portfolio_balance(user_id: int, update_data: Dict[str, Any]) -> bool:
    """Update a user's portfolio balance and related fields."""
    db = get_db()
    
    # Get the existing portfolio
    portfolio = get_portfolio_by_user_id(user_id)
    if not portfolio:
        logger.error(f"Portfolio for user {user_id} not found")
        return False
    
    # Add timestamp for update
    update_data["updated_at"] = datetime.now()
    
    # Update the portfolio
    return db.update_row(Portfolio, update_data, "User_ID", user_id)

def create_portfolio(user_id: int) -> Dict[str, Any]:
    """Create a new portfolio for a user."""
    db = get_db()
    
    # Check if portfolio already exists
    portfolio = get_portfolio_by_user_id(user_id)
    if portfolio:
        logger.info(f"Portfolio already exists for user {user_id}")
        return portfolio
    
    # Create new portfolio
    portfolio_data = {
        "User_ID": user_id,
        "balance": 10000.0,  # Default starting balance
        "profit_loss": 0.0,
        "created_at": datetime.now(),
        "updated_at": datetime.now()
    }
    
    success = db.insert_row(Portfolio, portfolio_data)
    
    if success:
        logger.info(f"Created new portfolio for user {user_id}")
        # Get the newly created portfolio
        return get_portfolio_by_user_id(user_id)
    else:
        return {"error": "Failed to create portfolio"}

def get_current_market_price(market: str = "Germany") -> float:
    """Get the current market price (latest price for the current hour)."""
    db = get_db()
    
    # Get the current hour
    now = datetime.now()
    current_hour = now.hour
    today = now.strftime('%Y-%m-%d')
    
    # Format the current period string
    current_period = f"{current_hour:02d}:00-{(current_hour+1):02d}:00"
    
    # Query for current hour's data
    def query_func(session):
        return session.query(MarketData).filter(
            MarketData.delivery_day == today,
            MarketData.market == market,
            MarketData.delivery_period == current_period
        ).first()
    
    current_data = db.execute_query(query_func)
    
    # If we have data, return the price
    if current_data:
        return current_data.get("close", 50.0)
    
    # If no data, create a synthetic price
    # Base price with time-of-day pattern and random variation
    base_price = 50 + 10 * math.sin(current_hour / 12 * math.pi)
    variation = random.uniform(-5, 5)
    current_price = round(base_price + variation, 2)
    
    return current_price 