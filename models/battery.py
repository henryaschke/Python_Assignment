from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class BatteryStatus(BaseModel):
    Battery_ID: int = Field(..., description="Battery ID")
    User_ID: int = Field(..., description="User ID")
    current_level: float = Field(..., description="Current battery level (percentage)")
    capacity: float = Field(..., description="Battery capacity in kWh")
    max_charge_rate: float = Field(..., description="Maximum charge rate in kW")
    max_discharge_rate: float = Field(..., description="Maximum discharge rate in kW")
    efficiency: float = Field(..., description="Battery efficiency (0-1)")
    current_energy: float = Field(..., description="Current energy in kWh")
    remaining_capacity: float = Field(..., description="Remaining capacity in kWh")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        from_attributes = True

class BatteryUpdate(BaseModel):
    current_level: float = Field(..., description="New battery level (percentage)") 