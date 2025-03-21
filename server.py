# Add a comment to mark this as the top-level package
# Python_Assignment is the package root

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import logging
import uvicorn
import os

# Import database for initialization
from Python_Assignment.database import get_db

# Import all route modules with updated package structure
from Python_Assignment.routes import auth, battery, forecast, market, performance, status, trade

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Energy Trading Platform API",
    description="API for energy trading platform with SQLite backend, real-time price data, battery management, and algorithm execution"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your domain(s)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers from all route modules
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(battery.router, prefix="/api/battery", tags=["Battery Management"])
app.include_router(forecast.router, prefix="/api/forecast", tags=["Forecasting"])
app.include_router(market.router, prefix="/api/market-data", tags=["Market Data"])
app.include_router(performance.router, prefix="/api/performance", tags=["Performance Metrics"])
app.include_router(status.router, prefix="/api", tags=["Diagnostics & Status"])
app.include_router(trade.router, prefix="/api/trades", tags=["Trading Operations"])

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

# Startup event to initialize the database
@app.on_event("startup")
async def startup_db_client():
    try:
        # Initialize the database and create tables
        db = get_db()
        logger.info("Database initialized successfully on startup")
    except Exception as e:
        logger.error(f"Error initializing database on startup: {e}")

# Main entry point
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True) 