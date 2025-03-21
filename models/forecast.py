from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ForecastPoint(BaseModel):
    id: int = Field(..., description="Forecast ID")
    timestamp: datetime = Field(..., description="Forecast timestamp")
    market: str = Field(..., description="Market identifier")
    predicted_price: float = Field(..., description="Predicted price")
    lower_bound: Optional[float] = Field(None, description="Lower confidence bound")
    upper_bound: Optional[float] = Field(None, description="Upper confidence bound")
    confidence: Optional[float] = Field(None, description="Confidence level (0-1)")
    created_at: datetime = Field(..., description="Creation timestamp")
    
    class Config:
        from_attributes = True

class ForecastRequest(BaseModel):
    market: str = Field("Germany", description="Market to forecast for")
    start_timestamp: Optional[datetime] = Field(None, description="Start timestamp")
    end_timestamp: Optional[datetime] = Field(None, description="End timestamp")
    
class ForecastResult(BaseModel):
    forecasts: List[ForecastPoint] = Field(..., description="List of forecast points") 