import json
from fastapi import HTTPException
from repositories.connection import get_connection

def list_medicines_transaction(owner):
    with get_connection() as connection:
        if owner:
            rows = connection.execute('SELECT * FROM medicines WHERE owner = ? ORDER BY id DESC', (owner,)).fetchall()
        else:
            rows = connection.execute('SELECT * FROM medicines ORDER BY id DESC').fetchall()
    return (rows,)

def get_medicine_transaction(medicine_id):
    with get_connection() as connection:
        row = connection.execute('SELECT * FROM medicines WHERE id = ?', (medicine_id,)).fetchone()
    return (row,)

def create_medicine_transaction(expiry_date, medicine, production_date, shelf_life):
    with get_connection() as connection:
        cursor = connection.execute("\n            INSERT INTO medicines\n                (emoji, name, spec, category, owner, dose, frequency, meal_time,\n                 method, location, production_date, shelf_life, expiry_date,\n                 stock, status, risks, note,\n                 original_text, created_at)\n            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))\n            ", (medicine.emoji, medicine.name, medicine.spec, medicine.category, medicine.owner, medicine.dose, medicine.frequency, medicine.meal_time, medicine.method, medicine.location, production_date, shelf_life, expiry_date, medicine.stock, medicine.status, json.dumps(medicine.risks, ensure_ascii=False), medicine.note, medicine.original_text))
        row = connection.execute('SELECT * FROM medicines WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return (row,)

def update_medicine_transaction(expiry_date, medicine, medicine_id, production_date, shelf_life):
    with get_connection() as connection:
        existing = connection.execute('SELECT id FROM medicines WHERE id = ?', (medicine_id,)).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail='药品不存在')
        connection.execute('\n            UPDATE medicines\n            SET emoji = ?, name = ?, spec = ?, category = ?, owner = ?,\n                dose = ?, frequency = ?, meal_time = ?, method = ?,\n                location = ?, production_date = ?, shelf_life = ?,\n                expiry_date = ?, stock = ?, status = ?,\n                risks = ?, note = ?, original_text = ?\n            WHERE id = ?\n            ', (medicine.emoji, medicine.name, medicine.spec, medicine.category, medicine.owner, medicine.dose, medicine.frequency, medicine.meal_time, medicine.method, medicine.location, production_date, shelf_life, expiry_date, medicine.stock, medicine.status, json.dumps(medicine.risks, ensure_ascii=False), medicine.note, medicine.original_text, medicine_id))
        row = connection.execute('SELECT * FROM medicines WHERE id = ?', (medicine_id,)).fetchone()
    return (row,)

def delete_medicine_transaction(medicine_id):
    with get_connection() as connection:
        medicine = connection.execute('SELECT id FROM medicines WHERE id = ?', (medicine_id,)).fetchone()
        if medicine is None:
            raise HTTPException(status_code=404, detail='药品不存在')
        connection.execute('\n            UPDATE reminders\n            SET is_active = 0\n            WHERE medicine_id = ? AND is_active = 1\n            ', (medicine_id,))
        connection.execute('DELETE FROM medicines WHERE id = ?', (medicine_id,))
