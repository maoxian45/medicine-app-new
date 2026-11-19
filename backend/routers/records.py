from fastapi import APIRouter, Query, status
from models.records import RecordCreate, RecordResponse
from services import records as service
router = APIRouter(prefix='/api/records', tags=['服药记录'])

@router.get('', response_model=list[RecordResponse])
def list_records(date: str | None=Query(default=None, description='单日日期，格式 YYYY-MM-DD'), member_id: int | None=Query(default=None, description='按家庭成员筛选'), medicine_id: int | None=Query(default=None, description='按药品筛选'), start_date: str | None=Query(default=None, description='开始日期，格式 YYYY-MM-DD'), end_date: str | None=Query(default=None, description='结束日期，格式 YYYY-MM-DD')) -> list[dict]:
    return service.list_records(date, member_id, medicine_id, start_date, end_date)

@router.post('', response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(record: RecordCreate) -> dict:
    return service.create_record(record)

@router.delete('/{record_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: int) -> None:
    return service.delete_record(record_id)
