from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MarketDataPoint(BaseModel):
    id: int = Field(..., description="Market data ID")
    delivery_day: str = Field(..., description="Delivery day in YYYY-MM-DD format")
    delivery_period: str = Field(..., description="Delivery period e.g. '12:00-13:00'")
    cleared: bool = Field(..., description="Whether the contract has cleared")
    market: str = Field(..., description="Market name")
    high: Optional[float] = Field(None, description="Highest price")
    low: Optional[float] = Field(None, description="Lowest price")
    close: Optional[float] = Field(None, description="Closing price")
    open: Optional[float] = Field(None, description="Opening price")
    transaction_volume: Optional[float] = Field(None, description="Transaction volume")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True

class MarketDataFilter(BaseModel):
    start_date: Optional[str] = Field(None, description="Start date in YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="End date in YYYY-MM-DD format")
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")
    market: str = Field("Germany", description="Market identifier")

class HistoricalMarketDataPoint(BaseModel):
    id: int = Field(..., description="Unique ID")
    date: str = Field(..., description="Delivery date")
    resolution: str = Field(..., description="Time resolution (e.g. '15min')")
    delivery_period: str = Field(..., description="Time period")
    market: str = Field(..., description="Market identifier")
    high_price: Optional[float] = Field(None, description="Highest price")
    low_price: Optional[float] = Field(None, description="Lowest price")
    average_price: Optional[float] = Field(None, description="Average price (VWAP)")
    open_price: Optional[float] = Field(None, description="Opening price")
    close_price: Optional[float] = Field(None, description="Closing price")
    buy_volume: Optional[float] = Field(None, description="Buy volume")
    sell_volume: Optional[float] = Field(None, description="Sell volume")
    volume: Optional[float] = Field(None, description="Total volume")
    vwap3h: Optional[float] = Field(None, description="3-hour volume-weighted average price")
    vwap1h: Optional[float] = Field(None, description="1-hour volume-weighted average price")
    contract_open_time: Optional[str] = Field(None, description="Time contract opened")
    contract_close_time: Optional[str] = Field(None, description="Time contract closed")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True 