from pydantic import BaseModel

class TodayItem(BaseModel):
    medicine_id: int | None = None
    reminder_id: int
    medicine_name: str
    member_name: str
    time: str
    meal_label: str
    dose: str
    status: str
    record_id: int | None = None
    taken_at: str | None = None

class TodayResponse(BaseModel):
    date: str
    total: int
    completed: int
    pending: int
    items: list[TodayItem]
