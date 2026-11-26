from fastapi import APIRouter

from models.instruction import (
    InstructionParseRequest,
    InstructionParseResponse,
    SampleMedicineSummary,
)
from services import instruction as service

router = APIRouter(prefix='/api/instruction', tags=['说明书解析'])


@router.get(
    '/samples',
    response_model=list[SampleMedicineSummary],
    summary='查询说明书样例',
)
def list_instruction_samples() -> list[dict[str, str]]:
    """返回内置演示样例，供前端样例选择弹窗使用。"""

    return service.list_instruction_samples()


@router.post(
    '/parse',
    response_model=InstructionParseResponse,
    summary='解析说明书',
)
def parse_instruction_text(request: InstructionParseRequest) -> dict[str, object]:
    """ocr_text 与 sample_id 必须二选一。

    两者都给或都不给返回 400，样例 ID 不存在返回 404；响应里的
    missing_fields 用于提示用户补全必填项。
    """

    return service.parse_instruction_text(request)
