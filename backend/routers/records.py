from fastapi import APIRouter, Query, status

from models.records import RecordCreate, RecordResponse
from services import records as service

router = APIRouter(prefix='/api/records', tags=['服药记录'])


@router.get('', response_model=list[RecordResponse], summary='查询服药记录')
def list_records(
    date: str | None = Query(default=None, description='单日日期，格式 YYYY-MM-DD'),
    member_id: int | None = Query(default=None, description='按家庭成员筛选'),
    medicine_id: int | None = Query(default=None, description='按药品筛选'),
    start_date: str | None = Query(default=None, description='开始日期，格式 YYYY-MM-DD'),
    end_date: str | None = Query(default=None, description='结束日期，格式 YYYY-MM-DD'),
) -> list[dict]:
    """不传日期时默认查本机当天；同时传 date 和起止日期时以 date 为准。"""

    return service.list_records(date, member_id, medicine_id, start_date, end_date)


@router.post(
    '',
    response_model=RecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary='新增服药记录',
)
def create_record(record: RecordCreate) -> dict:
    """确认提醒或手动补录。

    手动补录可传 taken_at（必须带时区、不能晚于当前时间、不能和 reminder_id
    同时使用）；同一提醒当天重复确认返回 409，关联对象与名称不一致返回 422。
    """

    return service.create_record(record)


@router.delete(
    '/{record_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='撤销服药记录',
)
def delete_record(record_id: int) -> None:
    """记录不存在时返回 404。"""

    return service.delete_record(record_id)
