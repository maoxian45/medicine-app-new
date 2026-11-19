from pydantic import BaseModel, Field

class RecordCreate(BaseModel):
    reminder_id: int | None = None
    medicine_id: int | None = None
    member_id: int | None = None
    medicine_name: str = Field(min_length=1)
    member_name: str = Field(min_length=1)
    dose: str = ''
    recorded_by: str = ''
    temperature: str = ''
    note: str = ''
    status: str = '已服药'

class RecordResponse(RecordCreate):
    id: int
    taken_at: str
    created_at: str
