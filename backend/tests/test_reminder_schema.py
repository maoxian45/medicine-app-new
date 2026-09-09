"""提醒软删除字段的数据库迁移测试。"""

import sqlite3

from database import _migrate_reminders_schema


def test_migration_adds_active_flag_and_keeps_legacy_reminder_active() -> None:
    """旧提醒增加字段后默认有效，药品 ID 保持待补关联状态。"""

    connection = sqlite3.connect(":memory:")
    connection.execute(
        """
        CREATE TABLE reminders (
            id INTEGER PRIMARY KEY,
            medicine_name TEXT NOT NULL,
            member_name TEXT NOT NULL,
            time TEXT NOT NULL
        )
        """
    )
    connection.execute(
        """
        INSERT INTO reminders (medicine_name, member_name, time)
        VALUES ('旧提醒药品', '我', '08:00')
        """
    )

    _migrate_reminders_schema(connection)
    row = connection.execute(
        "SELECT medicine_id, is_active FROM reminders"
    ).fetchone()
    connection.close()

    assert row == (None, 1)
