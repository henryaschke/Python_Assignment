from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TradeRequest(BaseModel):
    type: str = Field(..., description="Trade type (buy/sell)")
    quantity: float = Field(..., description="Trade quantity in MWh")
    executionTime: str = Field(..., description="Scheduled time of execution in ISO format")
    resolution: int = Field(..., description="Market resolution in minutes (15, 30, or 60)")
    trade_id: Optional[int] = Field(None, description="Optional trade ID (integer)")
    user_id: Optional[int] = Field(None, description="User ID (can be provided from auth)")
    market: str = Field("Germany", description="Energy market (default: Germany)")

class TradeResponse(BaseModel):
    Trade_ID: int = Field(..., description="Trade ID")
    User_ID: int = Field(..., description="User ID")
    type: str = Field(..., description="Trade type (buy/sell)")
    quantity: float = Field(..., description="Trade quantity in MWh")
    price: Optional[float] = Field(None, description="Price at execution")
    status: str = Field(..., description="Trade status (pending/executed/cancelled)")
    execution_time: datetime = Field(..., description="Scheduled execution time")
    executed_at: Optional[datetime] = Field(None, description="Actual execution time")
    created_at: datetime = Field(..., description="Trade creation time")
    resolution: int = Field(..., description="Market resolution in minutes")
    market: str = Field(..., description="Energy market")
    
    class Config:
        from_attributes = True

class TradeStatusUpdate(BaseModel):
    status: str = Field(..., description="New trade status (executed/cancelled)")
    price: Optional[float] = Field(None, description="Price at execution")
    
class AlgorithmSettings(BaseModel):
    settings: dict = Field(..., description="Algorithm configuration parameters") 