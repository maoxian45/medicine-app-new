from pydantic import BaseModel, Field

class MemberCreate(BaseModel):
    emoji: str = '🙂'
    name: str = Field(min_length=1)
    role: str = ''
    status: str = ''
    age: str = ''
    weight: str = ''
    allergy: str = ''

class MemberResponse(MemberCreate):
    id: int
    created_at: str
