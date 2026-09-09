"""服药记录表迁移测试。"""

import sqlite3

from database import _migrate_records_schema


def test_migration_adds_child_record_fields_to_legacy_records() -> None:
    """旧服药记录升级后应保留原字段，并补齐儿童记录字段默认值。"""

    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE records (
            id INTEGER PRIMARY KEY,
            reminder_id INTEGER,
            medicine_name TEXT NOT NULL,
            member_name TEXT NOT NULL,
            dose TEXT NOT NULL,
            taken_at TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        INSERT INTO records
            (reminder_id, medicine_name, member_name, dose, taken_at, status, created_at)
        VALUES (1, '旧记录药品', '小宝', '5毫升', '2026-08-02T09:00:00+00:00', '已服药', '2026-08-02T09:00:00+00:00')
        """
    )

    _migrate_records_schema(connection)
    row = connection.execute(
        """
        SELECT medicine_id, member_id, recorded_by, temperature, note
        FROM records
        """
    ).fetchone()
    connection.close()

    assert row == (None, None, "", "", "")
