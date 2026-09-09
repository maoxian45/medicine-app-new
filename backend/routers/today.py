from datetime import date as Date

from fastapi import APIRouter, Query
from pydantic import BaseModel

from database import get_connection


router = APIRouter(prefix="/api/today", tags=["今日状态"])


class TodayItem(BaseModel):
    reminder_id: int
    medicine_name: str
    member_name: str
    time: str
    meal_label: str
    dose: str
    status: str
    record_id: int | None = None
    taken_at: str | None = None


class TodayResponse(BaseModel):
    date: str
    total: int
    completed: int
    pending: int
    items: list[TodayItem]


@router.get("", response_model=TodayResponse)
def get_today_status(
    date: str | None = Query(default=None, description="日期，格式 YYYY-MM-DD")
) -> dict:
    target_date = date or Date.today().isoformat()
    with get_connection() as connection:
        reminders = connection.execute(
            "SELECT * FROM reminders WHERE is_active = 1 ORDER BY time, id"
        ).fetchall()
        records = connection.execute(
            """
            SELECT * FROM records
            WHERE substr(taken_at, 1, 10) = ?
            ORDER BY taken_at, id
            """,
            (target_date,),
        ).fetchall()

    record_rows = [dict(row) for row in records]
    used_record_ids: set[int] = set()
    items: list[dict] = []

    for reminder_row in reminders:
        reminder = dict(reminder_row)
        matched_record = None

        for record in record_rows:
            if record["id"] in used_record_ids:
                continue
            if record["reminder_id"] == reminder["id"]:
                matched_record = record
                break

        if matched_record is None:
            for record in record_rows:
                if record["id"] in used_record_ids:
                    continue
                same_medicine = record["medicine_name"] == reminder["medicine_name"]
                same_member = record["member_name"] == reminder["member_name"]
                same_dose = not reminder["dose"] or record["dose"] == reminder["dose"]
                if same_medicine and same_member and same_dose:
                    matched_record = record
                    break

        if matched_record is not None:
            used_record_ids.add(matched_record["id"])

        items.append(
            {
                "reminder_id": reminder["id"],
                "medicine_name": reminder["medicine_name"],
                "member_name": reminder["member_name"],
                "time": reminder["time"],
                "meal_label": reminder["meal_label"],
                "dose": reminder["dose"],
                "status": "已服药" if matched_record else "待服药",
                "record_id": matched_record["id"] if matched_record else None,
                "taken_at": matched_record["taken_at"] if matched_record else None,
            }
        )

    completed = sum(item["status"] == "已服药" for item in items)
    return {
        "date": target_date,
        "total": len(items),
        "completed": completed,
        "pending": len(items) - completed,
        "items": items,
    }
