from fastapi import APIRouter
from models.instruction import InstructionParseRequest, InstructionParseResponse, SampleMedicineSummary
from services import instruction as service
router = APIRouter(prefix='/api/instruction', tags=['说明书解析'])

@router.get('/samples', response_model=list[SampleMedicineSummary])
def list_instruction_samples() -> list[dict[str, str]]:
    return service.list_instruction_samples()

@router.post('/parse', response_model=InstructionParseResponse)
def parse_instruction_text(request: InstructionParseRequest) -> dict[str, object]:
    return service.parse_instruction_text(request)
