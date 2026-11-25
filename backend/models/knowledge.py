from typing import Literal
from pydantic import BaseModel, Field, field_validator


class KnowledgeEntry(BaseModel):
    kind: Literal['drug', 'rule', 'food_rule', 'population_rule'] = 'drug'
    name: str = Field(min_length=1, max_length=160)
    aliases: list[str] = Field(default_factory=list)
    ingredients: list[str] = Field(default_factory=list)
    dosage: str = ''
    contraindications: str = ''
    precautions: str = ''
    special_population: str = ''
    food_notes: str = ''
    left: str = ''
    right: str = ''
    level: Literal['严重风险', '需关注', '一般提醒', '数据不足'] = '需关注'
    impact: str = ''
    advice: str = '请咨询医生或药师，不要自行停药、换药或调整剂量。'
    source_name: str = Field(min_length=1)
    source_url: str = Field(pattern=r'^https://')
    chapter: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    original: str = Field(min_length=1)

    @field_validator('name', 'source_name', 'chapter', 'source_version', 'original')
    @classmethod
    def not_blank(cls, value):
        if not value.strip():
            raise ValueError('不能为空白')
        return value.strip()


class LoginRequest(BaseModel):
    username: str
    password: str


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: int | None = None
    drug_name: str = Field(default='', max_length=160)


class AIConfig(BaseModel):
    base_url: str = Field(pattern=r'^https://')
    model: str = Field(min_length=1, max_length=160)
    api_key: str = Field(default='', max_length=2000)


class RiskCheck(BaseModel):
    member_id: int
    candidate_name: str = ''
    candidate_ingredients: list[str] = Field(default_factory=list)
    exclude_medicine_id: int | None = None
    foods: list[str] = Field(default_factory=list, max_length=30)


class Feedback(BaseModel):
    entry_id: int
    message: str = Field(min_length=1, max_length=2000)
