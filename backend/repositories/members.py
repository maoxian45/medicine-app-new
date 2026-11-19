from repositories.connection import get_connection

def list_members_transaction():
    with get_connection() as connection:
        rows = connection.execute('SELECT * FROM members ORDER BY id').fetchall()
    return (rows,)

def get_member_transaction(member_id):
    with get_connection() as connection:
        row = connection.execute('SELECT * FROM members WHERE id = ?', (member_id,)).fetchone()
    return (row,)

def create_member_transaction(member):
    with get_connection() as connection:
        cursor = connection.execute("\n                INSERT INTO members\n                    (emoji, name, role, status, age, weight, allergy, created_at)\n                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))\n                ", (member.emoji, member.name, member.role, member.status, member.age, member.weight, member.allergy))
        row = connection.execute('SELECT * FROM members WHERE id = ?', (cursor.lastrowid,)).fetchone()
    return (row,)

def delete_member_transaction(member_id):
    with get_connection() as connection:
        cursor = connection.execute('DELETE FROM members WHERE id = ?', (member_id,))
    return (cursor,)


def update_member_transaction(member_id, member):
    with get_connection() as c:
        old=c.execute('SELECT name FROM members WHERE id=?',(member_id,)).fetchone()
        if old is None: return None
        c.execute('UPDATE members SET emoji=?,name=?,role=?,status=?,age=?,weight=?,allergy=? WHERE id=?',
                  (member.emoji,member.name,member.role,member.status,member.age,member.weight,member.allergy,member_id))
        c.execute('UPDATE medicines SET owner=? WHERE owner=?',(member.name,old['name']))
        c.execute('UPDATE reminders SET member_name=? WHERE member_name=?',(member.name,old['name']))
        return dict(c.execute('SELECT * FROM members WHERE id=?',(member_id,)).fetchone())
