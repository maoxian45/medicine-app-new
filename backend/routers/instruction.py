"""药品说明书解析与样例选择接口。"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from services.instruction_parser import (
    build_sample_card,
    parse_instruction,
)
from services.sample_medicine_loader import (
    list_sample_summaries,
)


router = APIRouter(
    prefix="/api/instruction",
    tags=["说明书解析"],
)


class InstructionParseRequest(BaseModel):
    """OCR 文字和样例 ID 必须二选一。"""

    ocr_text: str | None = Field(
        default=None,
        min_length=1,
        description="iOS Vision 识别出的说明书原始文字",
    )

    sample_id: str | None = Field(
        default=None,
        min_length=1,
        description="用户从样例弹窗中选择的标准样例 ID",
    )


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


@router.get(
    "/samples",
    response_model=list[SampleMedicineSummary],
)
def list_instruction_samples() -> list[dict[str, str]]:
    """返回固定的五套标准样例。"""

    return list_sample_summaries()


@router.post(
    "/parse",
    response_model=InstructionParseResponse,
)
def parse_instruction_text(
    request: InstructionParseRequest,
) -> dict[str, object]:
    """通过 OCR 文字或样例 ID 生成结构化用药卡片。"""

    ocr_text = (
        request.ocr_text.strip()
        if request.ocr_text
        else ""
    )

    sample_id = (
        request.sample_id.strip()
        if request.sample_id
        else ""
    )

    has_ocr_text = bool(ocr_text)
    has_sample_id = bool(sample_id)

    # 两个字段必须且只能提供一个。
    if has_ocr_text == has_sample_id:
        raise HTTPException(
            status_code=400,
            detail=(
                "ocr_text 和 sample_id 必须二选一，"
                "不能同时提供，也不能同时为空"
            ),
        )

    # 用户主动选择样例模板。
    if has_sample_id:
        card = build_sample_card(sample_id)

        if card is None:
            raise HTTPException(
                status_code=404,
                detail=f"不存在样例药品：{sample_id}",
            )

        return card

    # 使用真实 OCR 文字解析，不自动套用样例数据。
    return parse_instruction(ocr_text)