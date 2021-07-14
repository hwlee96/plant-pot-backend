from pydantic import BaseModel
from enum import Enum
from typing import Union, Dict

class SensorType(str, Enum):
    temperature = "temperature"
    nutrient_level = "nutrientLevel"
    water_level = "waterLevel"

class SensorIndicatorRange(str, Enum):
    null = None
    low = "low"
    medium = "medium"
    high = "high"
    
class Sensor(BaseModel):
    type: SensorType
    value: Union[None, float] = None
    indicator: Union[None, SensorIndicatorRange] = SensorIndicatorRange.medium
    toAlert: bool = False
    class Config:  
        use_enum_values = True