from repositories import records as repository
from models.records import RecordCreate
from datetime import date as Date
from datetime import datetime, timezone
from fastapi import HTTPException, Query

def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def list_records(date: str | None=Query(default=None, description='单日日期，格式 YYYY-MM-DD'), member_id: int | None=Query(default=None, description='按家庭成员筛选'), medicine_id: int | None=Query(default=None, description='按药品筛选'), start_date: str | None=Query(default=None, description='开始日期，格式 YYYY-MM-DD'), end_date: str | None=Query(default=None, description='结束日期，格式 YYYY-MM-DD')) -> list[dict]:
    filters: list[str] = []
    values: list[object] = []

    def parse_date(value: str, field_name: str) -> str:
        try:
            return Date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=f'{field_name} 必须使用 YYYY-MM-DD 格式') from exc
    if date is not None:
        filters.append('substr(taken_at, 1, 10) = ?')
        values.append(parse_date(date, 'date'))
    elif start_date is not None or end_date is not None:
        parsed_start_date = parse_date(start_date, 'start_date') if start_date else None
        parsed_end_date = parse_date(end_date, 'end_date') if end_date else None
        if parsed_start_date and parsed_end_date and (parsed_start_date > parsed_end_date):
            raise HTTPException(status_code=422, detail='start_date 不能晚于 end_date')
        if parsed_start_date:
            filters.append('substr(taken_at, 1, 10) >= ?')
            values.append(parsed_start_date)
        if parsed_end_date:
            filters.append('substr(taken_at, 1, 10) <= ?')
            values.append(parsed_end_date)
    elif member_id is None and medicine_id is None:
        filters.append('substr(taken_at, 1, 10) = ?')
        values.append(Date.today().isoformat())
    if member_id is not None:
        filters.append('member_id = ?')
        values.append(member_id)
    if medicine_id is not None:
        filters.append('medicine_id = ?')
        values.append(medicine_id)
    where_clause = ' WHERE ' + ' AND '.join(filters) if filters else ''
    rows, = repository.list_records_transaction(values, where_clause)
    return [dict(row) for row in rows]

def create_record(record: RecordCreate) -> dict:
    row, = repository.create_record_transaction(_now, record)
    return dict(row)

def delete_record(record_id: int) -> None:
    """撤销一次服药确认，删除对应的服药记录。"""
    cursor, = repository.delete_record_transaction(record_id)
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail='服药记录不存在')
