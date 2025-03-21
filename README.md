# Energy Trading Platform API

A FastAPI-based platform for energy trading with battery management, market data, and forecasting capabilities.

## Project Structure

The application is organized as a Python package:

```
Python_Assignment/           # Main package
├── auth/                   # Authentication modules
│   ├── __init__.py
│   └── dependencies.py     # Authentication functions
├── models/                 # Pydantic models
│   ├── __init__.py
│   ├── auth.py
│   ├── battery.py
│   ├── forecast.py
│   ├── market.py
│   └── trade.py
├── routes/                 # API endpoints
│   ├── __init__.py
│   ├── auth.py
│   ├── battery.py
│   ├── forecast.py
│   ├── market.py
│   ├── performance.py
│   ├── status.py
│   └── trade.py
├── utils/                  # Utility functions
├── __init__.py             # Package init
├── database.py             # Database connection and queries
├── server.py               # FastAPI application
├── seed_database.py        # Data seeding script
├── test_api.ps1            # PowerShell test script
└── requirements.txt        # Python dependencies
```

## Running the API

**IMPORTANT**: To run the application correctly, use the `run.py` script at the project root:

```bash
# From the project root (not inside Python_Assignment)
python run.py
```

The API will be available at http://localhost:8000

## API Documentation

- API documentation is available at http://localhost:8000/docs when the server is running
- Redoc alternative documentation is at http://localhost:8000/redoc

## Testing

Run the API tests using PowerShell:

```bash
cd Python_Assignment
powershell -ExecutionPolicy Bypass -File test_api.ps1
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register a new user
- `POST /api/auth/login` - Login and get an access token
- `POST /api/auth/token` - Get an access token (OAuth2 flow)
- `GET /api/auth/me` - Get current user information

### Status
- `GET /api/status` - Get server status and diagnostics
- `GET /api/whoami` - Get authenticated user info

### Battery Management
- `GET /api/battery/status` - Get battery status
- `POST /api/battery/charge` - Charge the battery
- `POST /api/battery/discharge` - Discharge the battery

### Market Data
- `GET /api/market-data/` - Get historical market data
- `GET /api/market-data/today` - Get today's market data
- `GET /api/market-data/current-price` - Get current market price

### Forecasting
- `GET /api/forecast/prices` - Get price forecasts
- `GET /api/forecast/accuracy` - Get forecast accuracy metrics

### Performance Metrics
- `GET /api/performance/portfolio` - Get portfolio performance metrics
- `GET /api/performance/battery-utilization` - Get battery utilization metrics
- `GET /api/performance/trade-pnl` - Calculate profit/loss from executed trades

### Trading Operations
- `GET /api/trades/` - Get all trades for a user
- `POST /api/trades/` - Create a new trade
- `POST /api/trades/buy` - Buy electricity (with immediate execution)
- `POST /api/trades/sell` - Sell electricity (with immediate execution)
- `GET /api/trades/{trade_id}` - Get a specific trade
- `PATCH /api/trades/{trade_id}` - Update a trade 