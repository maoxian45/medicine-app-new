from fastapi import HTTPException
from repositories.connection import get_connection

def set_state(reminder_id,active):
    with get_connection() as c:
        cursor=c.execute('UPDATE reminders SET is_active=? WHERE id=?',(int(active),reminder_id))
        return cursor.rowcount>0

def list_reminders_transaction(include_inactive):
    with get_connection() as connection:
        if include_inactive:
            rows = connection.execute('SELECT * FROM reminders ORDER BY time, id').fetchall()
        else:
            rows = connection.execute('SELECT * FROM reminders WHERE is_active = 1 ORDER BY time, id').fetchall()
    return (rows,)

def get_reminder_transaction(reminder_id):
    with get_connection() as connection:
        row = connection.execute('SELECT * FROM reminders WHERE id = ?', (reminder_id,)).fetchone()
    return (row,)

def create_reminder_transaction(SHARED_MEMBER_NAMES, reminder):
    with get_connection() as connection:
        member_name = reminder.member_name.strip()
        if member_name in SHARED_MEMBER_NAMES:
            raise HTTPException(status_code=422, detail='提醒必须绑定具体家庭成员，不能设置为全部人')
        member = connection.execute('SELECT id FROM members WHERE name = ?', (member_name,)).fetchone()
        if member is None:
            raise HTTPException(status_code=404, detail='提醒对象成员不存在')
        if reminder.medicine_id is not None:
            medicine = connection.execute('SELECT id FROM medicines WHERE id = ?', (reminder.medicine_id,)).fetchone()
            if medicine is None:
                raise HTTPException(status_code=404, detail='关联药品不存在')
        cursor = connection.execute("\n            INSERT INTO reminders\n                (medicine_id, medicine_name, member_name, time, meal_label, dose,\n                 status, is_active, created_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?, 1, datetime('now'))\n            ", (reminder.medicine_id, reminder.medicine_name, member_name, reminder.time, reminder.meal_label, reminder.dose, reminder.status))
        row = connection.execute('SELECT * FROM reminders WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return (row,)

def delete_reminder_transaction(reminder_id):
    with get_connection() as connection:
        reminder = connection.execute('SELECT id FROM reminders WHERE id = ?', (reminder_id,)).fetchone()
        if reminder is None:
            raise HTTPException(status_code=404, detail='提醒计划不存在')
        has_records = connection.execute('SELECT 1 FROM records WHERE reminder_id = ? LIMIT 1', (reminder_id,)).fetchone()
        if has_records is None:
            connection.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
        else:
            connection.execute('UPDATE reminders SET is_active = 0 WHERE id = ?', (reminder_id,))
