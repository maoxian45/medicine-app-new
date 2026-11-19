from pydantic import BaseModel, Field

class ReminderState(BaseModel):
    is_active: bool
SHARED_MEMBER_NAMES = {'全部', '全部人', '所有人'}

class ReminderCreate(BaseModel):
    medicine_id: int | None = None
    medicine_name: str = Field(min_length=1)
    member_name: str = Field(min_length=1)
    time: str = Field(pattern=r'^([01]\d|2[0-3]):[0-5]\d$', description='24 小时制时间，例如 08:00')
    meal_label: str = ''
    dose: str = ''
    status: str = '待确认'

class ReminderResponse(ReminderCreate):
    id: int
    is_active: bool = True
    created_at: str
