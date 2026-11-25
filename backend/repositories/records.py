from fastapi import HTTPException
from repositories.connection import get_connection

def list_records_transaction(values, where_clause):
    with get_connection() as connection:
        rows = connection.execute(f'SELECT * FROM records{where_clause} ORDER BY taken_at DESC, id DESC', values).fetchall()
    return (rows,)

def create_record_transaction(_now, record, taken_at=None):
    with get_connection() as connection:
        created_at = _now()
        taken_at = taken_at or created_at
        if record.medicine_id is not None:
            medicine = connection.execute('SELECT name FROM medicines WHERE id = ?', (record.medicine_id,)).fetchone()
            if medicine is None:
                raise HTTPException(status_code=404, detail='关联药品不存在')
            if record.medicine_name.strip() != medicine['name']:
                raise HTTPException(status_code=422, detail='服药记录药品必须与 medicine_id 对应药品一致')
        if record.member_id is not None:
            member = connection.execute('SELECT name FROM members WHERE id = ?', (record.member_id,)).fetchone()
            if member is None:
                raise HTTPException(status_code=404, detail='关联家庭成员不存在')
            if record.member_name.strip() != member['name']:
                raise HTTPException(status_code=422, detail='服药记录成员必须与 member_id 对应成员一致')
        if record.reminder_id is not None:
            reminder = connection.execute('\n                SELECT id, medicine_name, member_name, dose\n                FROM reminders\n                WHERE id = ?\n                ', (record.reminder_id,)).fetchone()
            if reminder is None:
                raise HTTPException(status_code=404, detail='关联的提醒计划不存在')
            if record.member_name.strip() != reminder['member_name']:
                raise HTTPException(status_code=422, detail='服药记录成员必须与提醒对象一致')
            if record.medicine_name.strip() != reminder['medicine_name']:
                raise HTTPException(status_code=422, detail='服药记录药品必须与提醒药品一致')
            if reminder['dose'] and record.dose.strip() != reminder['dose']:
                raise HTTPException(status_code=422, detail='服药记录剂量必须与提醒剂量一致')
            existing_record = connection.execute('\n                SELECT id FROM records\n                WHERE reminder_id = ? AND substr(taken_at, 1, 10) = ?\n                ', (record.reminder_id, taken_at[:10])).fetchone()
            if existing_record is not None:
                raise HTTPException(status_code=409, detail='该提醒今日已确认服药，请勿重复提交')
        cursor = connection.execute('\n            INSERT INTO records\n                (reminder_id, medicine_id, member_id, medicine_name, member_name,\n                 dose, recorded_by, temperature, note, taken_at, status, created_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)\n            ', (record.reminder_id, record.medicine_id, record.member_id, record.medicine_name, record.member_name, record.dose, record.recorded_by, record.temperature, record.note, taken_at, record.status, created_at))
        row = connection.execute('SELECT * FROM records WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return (row,)

def delete_record_transaction(record_id):
    with get_connection() as connection:
        cursor = connection.execute('DELETE FROM records WHERE id = ?', (record_id,))
    return (cursor,)
