"""SQLite connection and first-version schema initialization."""

from datetime import datetime, timezone
from pathlib import Path
import sqlite3


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATABASE_PATH = DATA_DIR / "medicine.db"


def get_connection() -> sqlite3.Connection:
    """Create a SQLite connection with dictionary-like rows enabled."""

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _migrate_medicines_schema(connection: sqlite3.Connection) -> None:
    """Bring the medicines table in line with the final API contract."""

    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(medicines)").fetchall()
    }

    if "expiry_date" not in columns and "expiry" in columns:
        connection.execute(
            "ALTER TABLE medicines RENAME COLUMN expiry TO expiry_date"
        )
    elif "expiry_date" not in columns:
        connection.execute(
            "ALTER TABLE medicines ADD COLUMN expiry_date TEXT NOT NULL DEFAULT ''"
        )

    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(medicines)").fetchall()
    }
    if "production_date" not in columns:
        connection.execute(
            "ALTER TABLE medicines ADD COLUMN production_date TEXT NOT NULL DEFAULT ''"
        )
    if "shelf_life" not in columns:
        connection.execute(
            "ALTER TABLE medicines ADD COLUMN shelf_life TEXT NOT NULL DEFAULT '36个月'"
        )

    # 旧版本把“36个月”放在 expiry_date 中；它实际属于保质期，而非具体有效期。
    connection.execute(
        """
        UPDATE medicines
        SET shelf_life = '36个月', expiry_date = ''
        WHERE trim(expiry_date) = '36个月'
        """
    )
    connection.execute(
        """
        UPDATE medicines
        SET shelf_life = '36个月'
        WHERE trim(shelf_life) = ''
        """
    )


def _migrate_reminders_schema(connection: sqlite3.Connection) -> None:
    """增加提醒的药品关联和软删除标记，保留历史提醒与记录。"""

    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(reminders)").fetchall()
    }
    if "medicine_id" not in columns:
        connection.execute("ALTER TABLE reminders ADD COLUMN medicine_id INTEGER")
    if "is_active" not in columns:
        connection.execute(
            "ALTER TABLE reminders ADD COLUMN is_active INTEGER NOT NULL DEFAULT 1"
        )


def _migrate_records_schema(connection: sqlite3.Connection) -> None:
    """为儿童喂药记录补齐关联对象、记录人和观察信息字段。"""

    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(records)").fetchall()
    }
    additions = {
        "medicine_id": "INTEGER",
        "member_id": "INTEGER",
        "recorded_by": "TEXT NOT NULL DEFAULT ''",
        "temperature": "TEXT NOT NULL DEFAULT ''",
        "note": "TEXT NOT NULL DEFAULT ''",
    }
    for name, definition in additions.items():
        if name not in columns:
            connection.execute(f"ALTER TABLE records ADD COLUMN {name} {definition}")


def init_db() -> None:
    """Create the tables, migrate compatible local data, and seed members."""

    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emoji TEXT NOT NULL DEFAULT '🙂',
                name TEXT NOT NULL UNIQUE,
                role TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '',
                age TEXT NOT NULL DEFAULT '',
                weight TEXT NOT NULL DEFAULT '',
                allergy TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                emoji TEXT NOT NULL DEFAULT '💊',
                name TEXT NOT NULL,
                spec TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '',
                owner TEXT NOT NULL DEFAULT '',
                dose TEXT NOT NULL DEFAULT '',
                frequency TEXT NOT NULL DEFAULT '',
                meal_time TEXT NOT NULL DEFAULT '',
                method TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                production_date TEXT NOT NULL DEFAULT '',
                shelf_life TEXT NOT NULL DEFAULT '36个月',
                expiry_date TEXT NOT NULL DEFAULT '',
                stock TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '',
                risks TEXT NOT NULL DEFAULT '[]',
                note TEXT NOT NULL DEFAULT '',
                original_text TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER,
                medicine_name TEXT NOT NULL,
                member_name TEXT NOT NULL,
                time TEXT NOT NULL,
                meal_label TEXT NOT NULL DEFAULT '',
                dose TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT '待确认',
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reminder_id INTEGER,
                medicine_id INTEGER,
                member_id INTEGER,
                medicine_name TEXT NOT NULL,
                member_name TEXT NOT NULL,
                dose TEXT NOT NULL DEFAULT '',
                recorded_by TEXT NOT NULL DEFAULT '',
                temperature TEXT NOT NULL DEFAULT '',
                note TEXT NOT NULL DEFAULT '',
                taken_at TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT '已服药',
                created_at TEXT NOT NULL,
                FOREIGN KEY (reminder_id) REFERENCES reminders(id)
            );

            CREATE INDEX IF NOT EXISTS idx_records_taken_at
                ON records(taken_at);
            """
        )

        _migrate_medicines_schema(connection)
        _migrate_reminders_schema(connection)
        _migrate_records_schema(connection)

        existing_count = connection.execute(
            "SELECT COUNT(*) FROM members"
        ).fetchone()[0]
        if existing_count == 0:
            connection.executemany(
                """
                INSERT INTO members
                    (emoji, name, role, status, age, weight, allergy, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    ("👩", "我", "成人", "", "成人", "", "无", _now()),
                    ("👴", "爷爷", "老人慢病用药", "", "76 岁", "68kg", "无", _now()),
                    ("👵", "奶奶", "长期用药", "", "73 岁", "60kg", "无", _now()),
                    ("👶", "小宝", "儿童用药", "", "4 岁", "17kg", "青霉素", _now()),
                ],
            )
