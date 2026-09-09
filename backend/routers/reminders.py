import sqlite3

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from database import get_connection


router = APIRouter(prefix="/api/reminders", tags=["提醒计划"])

SHARED_MEMBER_NAMES = {"全部", "全部人", "所有人"}


class ReminderCreate(BaseModel):
    medicine_id: int | None = None
    medicine_name: str = Field(min_length=1)
    member_name: str = Field(min_length=1)
    time: str = Field(min_length=1, description="24 小时制时间，例如 08:00")
    meal_label: str = ""
    dose: str = ""
    status: str = "待确认"


class ReminderResponse(ReminderCreate):
    id: int
    is_active: bool = True
    created_at: str


@router.get("", response_model=list[ReminderResponse])
def list_reminders(include_inactive: bool = False) -> list[dict]:
    with get_connection() as connection:
        if include_inactive:
            rows = connection.execute(
                "SELECT * FROM reminders ORDER BY time, id"
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM reminders WHERE is_active = 1 ORDER BY time, id"
            ).fetchall()
    return [dict(row) for row in rows]


@router.get("/{reminder_id}", response_model=ReminderResponse)
def get_reminder(reminder_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM reminders WHERE id = ?", (reminder_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="提醒计划不存在")
    return dict(row)


@router.post("", response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(reminder: ReminderCreate) -> dict:
    with get_connection() as connection:
        member_name = reminder.member_name.strip()
        if member_name in SHARED_MEMBER_NAMES:
            raise HTTPException(
                status_code=422,
                detail="提醒必须绑定具体家庭成员，不能设置为全部人",
            )

        member = connection.execute(
            "SELECT id FROM members WHERE name = ?", (member_name,)
        ).fetchone()
        if member is None:
            raise HTTPException(status_code=404, detail="提醒对象成员不存在")

        if reminder.medicine_id is not None:
            medicine = connection.execute(
                "SELECT id FROM medicines WHERE id = ?", (reminder.medicine_id,)
            ).fetchone()
            if medicine is None:
                raise HTTPException(status_code=404, detail="关联药品不存在")

        cursor = connection.execute(
            """
            INSERT INTO reminders
                (medicine_id, medicine_name, member_name, time, meal_label, dose,
                 status, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))
            """,
            (
                reminder.medicine_id,
                reminder.medicine_name,
                member_name,
                reminder.time,
                reminder.meal_label,
                reminder.dose,
                reminder.status,
            ),
        )
        row = connection.execute(
            "SELECT * FROM reminders WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return dict(row)


@router.delete("/{reminder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int) -> None:
    """删除无记录提醒；有历史记录的提醒改为停用。"""

    with get_connection() as connection:
        reminder = connection.execute(
            "SELECT id FROM reminders WHERE id = ?", (reminder_id,)
        ).fetchone()
        if reminder is None:
            raise HTTPException(status_code=404, detail="提醒计划不存在")

        has_records = connection.execute(
            "SELECT 1 FROM records WHERE reminder_id = ? LIMIT 1", (reminder_id,)
        ).fetchone()
        if has_records is None:
            connection.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
        else:
            connection.execute(
                "UPDATE reminders SET is_active = 0 WHERE id = ?", (reminder_id,)
            )
