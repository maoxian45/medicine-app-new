from models.instruction import InstructionParseRequest
'药品说明书解析与样例选择接口。'
from fastapi import HTTPException
from services.instruction_parser import build_sample_card, parse_instruction
from services.sample_medicine_loader import list_sample_summaries

def list_instruction_samples() -> list[dict[str, str]]:
    """返回固定的五套标准样例。"""
    return list_sample_summaries()

def parse_instruction_text(request: InstructionParseRequest) -> dict[str, object]:
    """通过 OCR 文字或样例 ID 生成结构化用药卡片。"""
    ocr_text = request.ocr_text.strip() if request.ocr_text else ''
    sample_id = request.sample_id.strip() if request.sample_id else ''
    has_ocr_text = bool(ocr_text)
    has_sample_id = bool(sample_id)
    if has_ocr_text == has_sample_id:
        raise HTTPException(status_code=400, detail='ocr_text 和 sample_id 必须二选一，不能同时提供，也不能同时为空')
    if has_sample_id:
        card = build_sample_card(sample_id)
        if card is None:
            raise HTTPException(status_code=404, detail=f'不存在样例药品：{sample_id}')
        return card
    return parse_instruction(ocr_text)
