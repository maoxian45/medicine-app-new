from datetime import date as Date
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from database import get_connection


router = APIRouter(prefix="/api/records", tags=["服药记录"])


class RecordCreate(BaseModel):
    reminder_id: int | None = None
    medicine_id: int | None = None
    member_id: int | None = None
    medicine_name: str = Field(min_length=1)
    member_name: str = Field(min_length=1)
    dose: str = ""
    recorded_by: str = ""
    temperature: str = ""
    note: str = ""
    status: str = "已服药"


class RecordResponse(RecordCreate):
    id: int
    taken_at: str
    created_at: str


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@router.get("", response_model=list[RecordResponse])
def list_records(
    date: str | None = Query(default=None, description="单日日期，格式 YYYY-MM-DD"),
    member_id: int | None = Query(default=None, description="按家庭成员筛选"),
    medicine_id: int | None = Query(default=None, description="按药品筛选"),
    start_date: str | None = Query(default=None, description="开始日期，格式 YYYY-MM-DD"),
    end_date: str | None = Query(default=None, description="结束日期，格式 YYYY-MM-DD"),
) -> list[dict]:
    filters: list[str] = []
    values: list[object] = []

    def parse_date(value: str, field_name: str) -> str:
        try:
            return Date.fromisoformat(value).isoformat()
        except ValueError as exc:
            raise HTTPException(
                status_code=422,
                detail=f"{field_name} 必须使用 YYYY-MM-DD 格式",
            ) from exc

    if date is not None:
        filters.append("substr(taken_at, 1, 10) = ?")
        values.append(parse_date(date, "date"))
    elif start_date is not None or end_date is not None:
        parsed_start_date = parse_date(start_date, "start_date") if start_date else None
        parsed_end_date = parse_date(end_date, "end_date") if end_date else None
        if parsed_start_date and parsed_end_date and parsed_start_date > parsed_end_date:
            raise HTTPException(status_code=422, detail="start_date 不能晚于 end_date")
        if parsed_start_date:
            filters.append("substr(taken_at, 1, 10) >= ?")
            values.append(parsed_start_date)
        if parsed_end_date:
            filters.append("substr(taken_at, 1, 10) <= ?")
            values.append(parsed_end_date)
    elif member_id is None and medicine_id is None:
        # 保持旧前端 GET /api/records 默认只读取今日记录的行为。
        filters.append("substr(taken_at, 1, 10) = ?")
        values.append(Date.today().isoformat())

    if member_id is not None:
        filters.append("member_id = ?")
        values.append(member_id)
    if medicine_id is not None:
        filters.append("medicine_id = ?")
        values.append(medicine_id)

    where_clause = " WHERE " + " AND ".join(filters) if filters else ""
    with get_connection() as connection:
        rows = connection.execute(
            f"SELECT * FROM records{where_clause} ORDER BY taken_at DESC, id DESC",
            values,
        ).fetchall()
    return [dict(row) for row in rows]


@router.post("", response_model=RecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(record: RecordCreate) -> dict:
    with get_connection() as connection:
        taken_at = _now()
        if record.medicine_id is not None:
            medicine = connection.execute(
                "SELECT name FROM medicines WHERE id = ?", (record.medicine_id,)
            ).fetchone()
            if medicine is None:
                raise HTTPException(status_code=404, detail="关联药品不存在")
            if record.medicine_name.strip() != medicine["name"]:
                raise HTTPException(
                    status_code=422,
                    detail="服药记录药品必须与 medicine_id 对应药品一致",
                )

        if record.member_id is not None:
            member = connection.execute(
                "SELECT name FROM members WHERE id = ?", (record.member_id,)
            ).fetchone()
            if member is None:
                raise HTTPException(status_code=404, detail="关联家庭成员不存在")
            if record.member_name.strip() != member["name"]:
                raise HTTPException(
                    status_code=422,
                    detail="服药记录成员必须与 member_id 对应成员一致",
                )

        if record.reminder_id is not None:
            reminder = connection.execute(
                """
                SELECT id, medicine_name, member_name, dose
                FROM reminders
                WHERE id = ?
                """,
                (record.reminder_id,),
            ).fetchone()
            if reminder is None:
                raise HTTPException(status_code=404, detail="关联的提醒计划不存在")

            if record.member_name.strip() != reminder["member_name"]:
                raise HTTPException(
                    status_code=422,
                    detail="服药记录成员必须与提醒对象一致",
                )
            if record.medicine_name.strip() != reminder["medicine_name"]:
                raise HTTPException(
                    status_code=422,
                    detail="服药记录药品必须与提醒药品一致",
                )
            if reminder["dose"] and record.dose.strip() != reminder["dose"]:
                raise HTTPException(
                    status_code=422,
                    detail="服药记录剂量必须与提醒剂量一致",
                )

            existing_record = connection.execute(
                """
                SELECT id FROM records
                WHERE reminder_id = ? AND substr(taken_at, 1, 10) = ?
                """,
                (record.reminder_id, taken_at[:10]),
            ).fetchone()
            if existing_record is not None:
                raise HTTPException(
                    status_code=409,
                    detail="该提醒今日已确认服药，请勿重复提交",
                )

        cursor = connection.execute(
            """
            INSERT INTO records
                (reminder_id, medicine_id, member_id, medicine_name, member_name,
                 dose, recorded_by, temperature, note, taken_at, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.reminder_id,
                record.medicine_id,
                record.member_id,
                record.medicine_name,
                record.member_name,
                record.dose,
                record.recorded_by,
                record.temperature,
                record.note,
                taken_at,
                record.status,
                taken_at,
            ),
        )
        row = connection.execute(
            "SELECT * FROM records WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return dict(row)


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_record(record_id: int) -> None:
    """撤销一次服药确认，删除对应的服药记录。"""

    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM records WHERE id = ?", (record_id,))

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="服药记录不存在")
