"""Knowledge, audit, sessions, confirmed fields. Owner: wzy."""
import json
from pathlib import Path
from datetime import datetime, timezone
from database import get_connection


def now():
    return datetime.now(timezone.utc).isoformat(timespec='seconds')


def initialize():
    with get_connection() as c:
        c.executescript('''
        CREATE TABLE IF NOT EXISTS knowledge_entries (
          id INTEGER PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL,
          payload TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1,
          review_status TEXT NOT NULL DEFAULT 'draft', active INTEGER NOT NULL DEFAULT 1,
          updated_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS knowledge_versions (
          id INTEGER PRIMARY KEY, entry_id INTEGER NOT NULL, revision INTEGER NOT NULL,
          snapshot TEXT NOT NULL, action TEXT NOT NULL, actor TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS knowledge_feedback (
          id INTEGER PRIMARY KEY, entry_id INTEGER NOT NULL, message TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS auth_sessions (
          token TEXT PRIMARY KEY, role TEXT NOT NULL, expires_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS ai_sessions (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS ai_messages (
          id INTEGER PRIMARY KEY, session_id INTEGER NOT NULL, role TEXT NOT NULL,
          content TEXT NOT NULL, sources TEXT NOT NULL DEFAULT '[]', created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS medicine_confirmations (
          medicine_id INTEGER PRIMARY KEY, confirmed INTEGER NOT NULL, ingredients TEXT NOT NULL,
          confirmed_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS risk_confirmations (
          id INTEGER PRIMARY KEY, member_id INTEGER NOT NULL, medicine_id INTEGER NOT NULL,
          report TEXT NOT NULL, created_at TEXT NOT NULL);
        ''')
    if not entries(True):
        from models.knowledge import KnowledgeEntry
        seed=Path(__file__).resolve().parents[1]/'sample_data'/'knowledge_seed.json'
        for payload in json.loads(seed.read_text(encoding='utf-8')):
            save(KnowledgeEntry(**payload).model_dump(),action='课程资料草稿导入',actor='bootstrap')


def unpack(row):
    row = dict(row)
    payload = json.loads(row.pop('payload'))
    return {**payload, **row}


def entries(include_drafts=False):
    with get_connection() as c:
        where = '' if include_drafts else "WHERE active=1 AND review_status='approved'"
        return [unpack(r) for r in c.execute(f'SELECT * FROM knowledge_entries {where} ORDER BY id DESC')]


def entry(entry_id):
    with get_connection() as c:
        row = c.execute('SELECT * FROM knowledge_entries WHERE id=?', (entry_id,)).fetchone()
    return unpack(row) if row else None


def save(payload, entry_id=None, action='edit', actor='admin'):
    with get_connection() as c:
        if entry_id is None:
            entry_id = c.execute('INSERT INTO knowledge_entries(kind,name,payload,updated_at) VALUES(?,?,?,?)',
                                 (payload['kind'], payload['name'], json.dumps(payload, ensure_ascii=False), now())).lastrowid
        else:
            c.execute("UPDATE knowledge_entries SET kind=?,name=?,payload=?,revision=revision+1,review_status='draft',updated_at=? WHERE id=?",
                      (payload['kind'], payload['name'], json.dumps(payload, ensure_ascii=False), now(), entry_id))
        snapshot = unpack(c.execute('SELECT * FROM knowledge_entries WHERE id=?', (entry_id,)).fetchone())
        c.execute('INSERT INTO knowledge_versions(entry_id,revision,snapshot,action,actor,created_at) VALUES(?,?,?,?,?,?)',
                  (entry_id, snapshot['revision'], json.dumps(snapshot, ensure_ascii=False), action, actor, now()))
    return snapshot


def change_state(entry_id, status, active):
    with get_connection() as c:
        c.execute('UPDATE knowledge_entries SET review_status=?,active=?,revision=revision+1,updated_at=? WHERE id=?',
                  (status, active, now(), entry_id))
        snapshot = unpack(c.execute('SELECT * FROM knowledge_entries WHERE id=?', (entry_id,)).fetchone())
        c.execute('INSERT INTO knowledge_versions(entry_id,revision,snapshot,action,actor,created_at) VALUES(?,?,?,?,?,?)',
                  (entry_id, snapshot['revision'], json.dumps(snapshot, ensure_ascii=False), status, 'admin', now()))
    return snapshot


def history(entry_id):
    with get_connection() as c:
        return [{**dict(r), 'snapshot': json.loads(r['snapshot'])} for r in c.execute(
            'SELECT * FROM knowledge_versions WHERE entry_id=? ORDER BY id DESC', (entry_id,))]


def feedback(entry_id, message):
    with get_connection() as c:
        c.execute('INSERT INTO knowledge_feedback(entry_id,message,created_at) VALUES(?,?,?)',(entry_id,message,now()))


def feedback_list():
    with get_connection() as c:
        return [dict(r) for r in c.execute('SELECT * FROM knowledge_feedback ORDER BY id DESC')]


def add_token(token, role, expiry):
    with get_connection() as c:
        c.execute('DELETE FROM auth_sessions WHERE expires_at < strftime(\'%s\',\'now\')')
        c.execute('INSERT INTO auth_sessions VALUES(?,?,?)',(token,role,expiry))


def token_role(token, timestamp):
    with get_connection() as c:
        row=c.execute('SELECT role FROM auth_sessions WHERE token=? AND expires_at>?',(token,timestamp)).fetchone()
    return row['role'] if row else None


def revoke(token):
    with get_connection() as c:
        c.execute('DELETE FROM auth_sessions WHERE token=?',(token,))


def chat_sessions():
    with get_connection() as c:
        return [dict(r) for r in c.execute('SELECT * FROM ai_sessions ORDER BY id DESC')]


def new_chat(title):
    with get_connection() as c:
        return c.execute('INSERT INTO ai_sessions(title,created_at) VALUES(?,?)',(title[:40],now())).lastrowid


def messages(session_id):
    with get_connection() as c:
        exists=c.execute('SELECT id FROM ai_sessions WHERE id=?',(session_id,)).fetchone()
        if not exists: return None
        return [{**dict(r),'sources':json.loads(r['sources'])} for r in c.execute('SELECT * FROM ai_messages WHERE session_id=? ORDER BY id',(session_id,))]


def add_exchange(session_id, question, answer, sources):
    with get_connection() as c:
        for role,content,refs in [('user',question,[]),('assistant',answer,sources)]:
            c.execute('INSERT INTO ai_messages(session_id,role,content,sources,created_at) VALUES(?,?,?,?,?)',
                      (session_id,role,content,json.dumps(refs,ensure_ascii=False),now()))


def confirmation(medicine_id, confirmed, ingredients):
    with get_connection() as c:
        c.execute('INSERT OR REPLACE INTO medicine_confirmations VALUES(?,?,?,?)',
                  (medicine_id,int(confirmed),json.dumps(ingredients,ensure_ascii=False),now()))


def confirmed(medicine_id):
    with get_connection() as c:
        row=c.execute('SELECT * FROM medicine_confirmations WHERE medicine_id=?',(medicine_id,)).fetchone()
    return bool(row and row['confirmed'])


def medicine_ingredients(medicine_id):
    with get_connection() as c:
        row=c.execute('SELECT ingredients FROM medicine_confirmations WHERE medicine_id=?',(medicine_id,)).fetchone()
    return json.loads(row['ingredients']) if row else []


def save_risk_confirmation(member_id,medicine_id,report):
    with get_connection() as c:
        c.execute('INSERT INTO risk_confirmations(member_id,medicine_id,report,created_at) VALUES(?,?,?,?)',
                  (member_id,medicine_id,json.dumps(report,ensure_ascii=False),now()))
