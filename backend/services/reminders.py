from repositories import reminders as repository

def set_state(reminder_id,active):
    from fastapi import HTTPException
    if not repository.set_state(reminder_id,active): raise HTTPException(404,'提醒不存在')
    return {'is_active':active}
from models.reminders import ReminderCreate
from fastapi import HTTPException
SHARED_MEMBER_NAMES = {'全部', '全部人', '所有人'}

def list_reminders(include_inactive: bool=False) -> list[dict]:
    rows, = repository.list_reminders_transaction(include_inactive)
    return [dict(row) for row in rows]

def get_reminder(reminder_id: int) -> dict:
    row, = repository.get_reminder_transaction(reminder_id)
    if row is None:
        raise HTTPException(status_code=404, detail='提醒计划不存在')
    return dict(row)

def create_reminder(reminder: ReminderCreate) -> dict:
    row, = repository.create_reminder_transaction(SHARED_MEMBER_NAMES, reminder)
    return dict(row)

def delete_reminder(reminder_id: int) -> None:
    """删除无记录提醒；有历史记录的提醒改为停用。"""
    repository.delete_reminder_transaction(reminder_id)
