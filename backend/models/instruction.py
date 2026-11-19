from pydantic import BaseModel, Field

class InstructionParseRequest(BaseModel):
    """OCR 文字和样例 ID 必须二选一。"""
    ocr_text: str | None = Field(default=None, min_length=1, description='iOS Vision 识别出的说明书原始文字')
    sample_id: str | None = Field(default=None, min_length=1, description='用户从样例弹窗中选择的标准样例 ID')

class InstructionParseResponse(BaseModel):
    """说明书解析后生成的用药卡片。"""
    emoji: str
    name: str
    spec: str
    category: str
    owner: str
    dose: str
    frequency: str
    meal_time: str
    method: str
    location: str
    expiry: str
    expiry_text: str
    stock: str
    status: str
    risks: list[str]
    contraindications: list[str]
    precautions: list[str]
    note: str
    original_text: str
    speech_text: str
    elder_speech_text: str
    needs_confirmation: bool
    data_source: str
    used_sample_fallback: bool
    sample_id: str
    fallback_fields: list[str]
    parse_quality: str
    missing_fields: list[str]
    demo_only: bool

class SampleMedicineSummary(BaseModel):
    """前端样例选择弹窗显示的简要数据。"""
    id: str
    name: str
    emoji: str
    category: str
    expiry_text: str
