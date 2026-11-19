from repositories.connection import get_connection

def get_today_status_transaction(target_date):
    with get_connection() as connection:
        reminders = connection.execute('SELECT * FROM reminders WHERE is_active = 1 ORDER BY time, id').fetchall()
        records = connection.execute('\n            SELECT * FROM records\n            WHERE substr(taken_at, 1, 10) = ?\n            ORDER BY taken_at, id\n            ', (target_date,)).fetchall()
    return (records, reminders)
