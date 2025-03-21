# 🔋 Energy Trading Platform API - Ein Projekt für Professor Alberto! 🔋

Hallo Professor Alberto! Welcome to my FastAPI-based platform for energy trading with battery management, market data, and forecasting capabilities. With German precision and technical excellence, this platform demonstrates a comprehensive energy trading ecosystem.

## 🚀 Project Structure - Ordnung muss sein!

The application is organized as a well-structured Python package:

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
├── test_api.ps1            # PowerShell test script (Check this out, Professor!)
└── requirements.txt        # Python dependencies
```

## 🏃‍♂️ Running the API - Let the Energy Flow!

**WICHTIG (IMPORTANT)**: To run the application correctly, use the `run.py` script at the project root:

```bash
# From the project root (not inside Python_Assignment)
python run.py
```

The API will be available at http://localhost:8000 - Pünktlich wie die deutsche Bahn... hoffentlich!

## 📚 API Documentation - For Your Reading Pleasure, Professor Alberto!

- API documentation is available at http://localhost:8000/docs when the server is running
- Redoc alternative documentation is at http://localhost:8000/redoc

## 🧪 Testing - Mit deutscher Präzision!

### 🌟 Special Interactive Test Script 🌟

Professor Alberto, I've created a special interactive test script just for you! It demonstrates all API endpoints with a touch of German flair:

```bash
cd Python_Assignment
powershell -ExecutionPolicy Bypass -File test_api.ps1
```

This script will walk you through all the functionalities with German phrases, English translations, and detailed technical information. It's both educational and entertaining! (Sehr interessant und unterhaltsam!)

Key features of the test script:
- Bilingual output with German phrases and English translations
- Clear endpoint information and request details
- Colorful and formatted output for better readability
- Technical details of requests and responses
- Personalized comments that make testing more enjoyable

## 📋 Project Requirements & Additional Features

### Core Requirements Implemented:
1. ✅ User Authentication System with JWT tokens
2. ✅ Battery Management System with charge/discharge functionality
3. ✅ Market Data API with historical and current price information
4. ✅ Trading Operations (buy/sell electricity)
5. ✅ Performance Metrics for portfolio analysis
6. ✅ Price Forecasting with accuracy metrics
7. ✅ API Documentation
8. ✅ Testing Suite
9. ✅ Database Implementation with SQLite
10. ✅ Error Handling and Validation

### Additional Features:
1. ✅ **Interactive Dashboard** - Beautiful UI for real-time monitoring
2. ✅ **Bilingual Test Script** - With German phrases and English translations
3. ✅ **Advanced Performance Metrics** - Including trade P&L calculations
4. ✅ **Battery Utilization Analytics** - Detailed insights into battery usage
5. ✅ **Data Seeding** - Automated script for populating test data
6. ✅ **Dockerization** - Container-ready with Dockerfile included
7. ✅ **Responsive Frontend** - Mobile-friendly user interface
8. ✅ **Custom Logging** - Detailed application logging for debugging
9. ✅ **Rate Limiting** - Protection against excessive API requests
10. ✅ **Role-Based Access Control** - Different permission levels for users

## 🔌 API Endpoints - The Technical Heart of the Project

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
- `GET /api/market-data/current` - Get current market data

### Forecasting
- `GET /api/forecast/price` - Get price forecasts
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

## 🎓 Final Note for Professor Alberto

I hope you enjoy exploring this Energy Trading Platform, Professor Alberto! I've put special effort into making it both technically robust and enjoyable to use. The combination of sound engineering principles and a touch of German flair makes for an educational and entertaining experience.

Vielen Dank für Ihre Zeit und Aufmerksamkeit!
(Thank you for your time and attention!) 