import re
from pydantic import BaseModel, Field
DEFAULT_SHELF_LIFE = '36个月'
SHELF_LIFE_PATTERN = re.compile('^(\\d+)\\s*个月$')

class MedicineFields(BaseModel):
    emoji: str = '💊'
    name: str = Field(min_length=1)
    spec: str = ''
    category: str = ''
    owner: str = ''
    dose: str = ''
    frequency: str = ''
    meal_time: str = ''
    method: str = ''
    location: str = ''
    production_date: str = ''
    shelf_life: str = DEFAULT_SHELF_LIFE
    expiry_date: str = ''
    stock: str = ''
    status: str = ''
    risks: list[str] = Field(default_factory=list)
    note: str = ''
    original_text: str = ''
    confirmed: bool = False
    ingredients: list[str] = Field(default_factory=list)
    risk_accepted: bool = False

class MedicineCreate(MedicineFields):
    pass

class MedicineUpdate(MedicineFields):
    pass

class MedicineResponse(MedicineFields):
    id: int
    created_at: str
