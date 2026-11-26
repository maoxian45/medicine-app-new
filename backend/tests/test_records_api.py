"""服药记录撤销接口自动化测试。"""

from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from database import init_db
from main import app


client = TestClient(app)


def _create_reminder_and_record() -> tuple[dict, dict]:
    medicine_name = f"撤销测试药品-{uuid4().hex[:8]}"
    reminder_response = client.post(
        "/api/reminders",
        json={
            "medicine_name": medicine_name,
            "member_name": "我",
            "time": "10:00",
            "dose": "1片",
        },
    )
    assert reminder_response.status_code == 201
    reminder = reminder_response.json()

    record_response = client.post(
        "/api/records",
        json={
            "reminder_id": reminder["id"],
            "medicine_name": medicine_name,
            "member_name": "我",
            "dose": "1片",
        },
    )
    assert record_response.status_code == 201
    return reminder, record_response.json()


def test_delete_record_restores_reminder_to_pending_today_status() -> None:
    """撤销服药记录后，今日状态应重新显示为待服药。"""

    reminder, record = _create_reminder_and_record()
    target_date = record["taken_at"][:10]

    before_response = client.get(f"/api/today?date={target_date}")
    before_item = next(
        item
        for item in before_response.json()["items"]
        if item["reminder_id"] == reminder["id"]
    )
    assert before_item["status"] == "已服药"
    assert before_item["record_id"] == record["id"]

    delete_response = client.delete(f"/api/records/{record['id']}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    after_response = client.get(f"/api/today?date={target_date}")
    after_item = next(
        item
        for item in after_response.json()["items"]
        if item["reminder_id"] == reminder["id"]
    )
    assert after_item["status"] == "待服药"
    assert after_item["record_id"] is None

    assert client.delete(f"/api/reminders/{reminder['id']}").status_code == 204


def test_delete_unknown_record_returns_404() -> None:
    """不存在的服药记录不能静默撤销。"""

    response = client.delete("/api/records/999999")
    assert response.status_code == 404


def test_create_record_rejects_duplicate_confirmation_for_same_reminder() -> None:
    """同一提醒当天不能重复生成服药记录。"""

    reminder, record = _create_reminder_and_record()

    duplicate_response = client.post(
        "/api/records",
        json={
            "reminder_id": reminder["id"],
            "medicine_name": reminder["medicine_name"],
            "member_name": reminder["member_name"],
            "dose": reminder["dose"],
        },
    )
    assert duplicate_response.status_code == 409
    assert "请勿重复提交" in duplicate_response.json()["detail"]

    assert client.delete(f"/api/records/{record['id']}").status_code == 204
    assert client.delete(f"/api/reminders/{reminder['id']}").status_code == 204


def test_create_record_must_match_its_reminder_details() -> None:
    """关联提醒时，成员、药品和已填写的剂量不能被篡改。"""

    reminder_response = client.post(
        "/api/reminders",
        json={
            "medicine_name": "记录一致性测试药",
            "member_name": "我",
            "time": "10:30",
            "dose": "1片",
        },
    )
    assert reminder_response.status_code == 201
    reminder = reminder_response.json()

    response = client.post(
        "/api/records",
        json={
            "reminder_id": reminder["id"],
            "medicine_name": reminder["medicine_name"],
            "member_name": "爷爷",
            "dose": reminder["dose"],
        },
    )
    assert response.status_code == 422
    assert "成员必须与提醒对象一致" in response.json()["detail"]

    assert client.delete(f"/api/reminders/{reminder['id']}").status_code == 204


def test_child_record_saves_observation_fields_and_supports_filters() -> None:
    """儿童喂药记录可保存关联信息，并按儿童、药品和日期范围查询。"""

    init_db()
    member_response = client.get("/api/members")
    child = next(item for item in member_response.json() if item["name"] == "小宝")
    medicine_response = client.post(
        "/api/medicines",
        json={"name": f"儿童喂药测试药-{uuid4().hex[:8]}"},
    )
    assert medicine_response.status_code == 201
    medicine = medicine_response.json()

    create_response = client.post(
        "/api/records",
        json={
            "medicine_id": medicine["id"],
            "member_id": child["id"],
            "medicine_name": medicine["name"],
            "member_name": child["name"],
            "dose": "5毫升",
            "recorded_by": "妈妈",
            "temperature": "37.2℃",
            "note": "饭后服用，精神正常",
            "status": "已服药",
        },
    )
    assert create_response.status_code == 201
    record = create_response.json()
    assert record["medicine_id"] == medicine["id"]
    assert record["member_id"] == child["id"]
    assert record["recorded_by"] == "妈妈"
    assert record["temperature"] == "37.2℃"
    assert record["note"] == "饭后服用，精神正常"

    # 记录按本机时区归档，用 UTC 字符串截日期会在上午 8 点前跑偏。
    day = datetime.fromisoformat(record["taken_at"]).astimezone().date().isoformat()
    query_response = client.get(
        "/api/records",
        params={
            "member_id": child["id"],
            "medicine_id": medicine["id"],
            "start_date": day,
            "end_date": day,
        },
    )
    assert query_response.status_code == 200
    assert record["id"] in {item["id"] for item in query_response.json()}

    assert client.delete(f"/api/records/{record['id']}").status_code == 204
    assert client.delete(f"/api/medicines/{medicine['id']}").status_code == 204


def test_manual_record_rejects_time_without_timezone() -> None:
    """手动补录的实际服药时间必须带时区，否则无法换算成本地日期。"""

    response = client.post(
        "/api/records",
        json={
            "medicine_name": "时区测试药",
            "member_name": "我",
            "taken_at": "2020-01-02T12:30:00",
        },
    )
    assert response.status_code == 422
    assert "时区" in response.json()["detail"]


def test_taken_at_is_rejected_for_reminder_records() -> None:
    """实际服药时间只用于手动补录，确认提醒时由服务端记录提交时间。"""

    reminder_response = client.post(
        "/api/reminders",
        json={
            "medicine_name": "补录限制测试药",
            "member_name": "我",
            "time": "11:00",
            "dose": "1片",
        },
    )
    assert reminder_response.status_code == 201
    reminder = reminder_response.json()

    response = client.post(
        "/api/records",
        json={
            "reminder_id": reminder["id"],
            "medicine_name": reminder["medicine_name"],
            "member_name": reminder["member_name"],
            "dose": reminder["dose"],
            "taken_at": "2020-01-02T12:30:00+08:00",
        },
    )
    assert response.status_code == 422
    assert "手动记录" in response.json()["detail"]

    assert client.delete(f"/api/reminders/{reminder['id']}").status_code == 204


def test_child_record_rejects_mismatched_link_fields() -> None:
    """儿童补录同时传 id 和名称时，两者必须指向同一条记录。"""

    init_db()
    medicine_response = client.post(
        "/api/medicines",
        json={"name": f"补录一致性测试药-{uuid4().hex[:8]}"},
    )
    assert medicine_response.status_code == 201
    medicine = medicine_response.json()
    child = next(
        item for item in client.get("/api/members").json() if item["name"] == "小宝"
    )

    mismatched_medicine = client.post(
        "/api/records",
        json={
            "medicine_id": medicine["id"],
            "medicine_name": "不是这个药",
            "member_id": child["id"],
            "member_name": child["name"],
        },
    )
    assert mismatched_medicine.status_code == 422
    assert "药品必须与 medicine_id" in mismatched_medicine.json()["detail"]

    mismatched_member = client.post(
        "/api/records",
        json={
            "medicine_id": medicine["id"],
            "medicine_name": medicine["name"],
            "member_id": child["id"],
            "member_name": "我",
        },
    )
    assert mismatched_member.status_code == 422
    assert "成员必须与 member_id" in mismatched_member.json()["detail"]

    assert client.delete(f"/api/medicines/{medicine['id']}").status_code == 204


def test_today_rejects_invalid_date_format() -> None:
    """今日状态接口的 date 必须使用 YYYY-MM-DD，非法格式返回 422。"""

    for value in ("abc", "2026-13-45"):
        response = client.get("/api/today", params={"date": value})
        assert response.status_code == 422
        assert "YYYY-MM-DD" in response.json()["detail"]

    response = client.get("/api/today", params={"date": "2026-11-26"})
    assert response.status_code == 200
    assert response.json()["date"] == "2026-11-26"


@pytest.mark.xfail(
    reason="wzy: /api/today 仍按 substr(taken_at,1,10) 取 UTC 日期，本地 0:00-7:59 的记录查不到",
    strict=False,
)
def test_today_matches_record_by_local_date() -> None:
    """本地清晨的记录，按本地日期查询今日状态时也应显示已服药。

    用「昨天 06:30（本地时区）」构造，避免测试结果受运行时刻影响。
    """

    local_now = datetime.now().astimezone()
    taken_at = (local_now - timedelta(days=1)).replace(
        hour=6, minute=30, second=0, microsecond=0
    )
    day = taken_at.date().isoformat()
    medicine_name = f"时区回归测试药-{uuid4().hex[:8]}"

    reminder_response = client.post(
        "/api/reminders",
        json={
            "medicine_name": medicine_name,
            "member_name": "我",
            "time": "06:30",
            "dose": "1片",
        },
    )
    assert reminder_response.status_code == 201
    reminder = reminder_response.json()

    record_response = client.post(
        "/api/records",
        json={
            "medicine_name": medicine_name,
            "member_name": "我",
            "dose": "1片",
            "taken_at": taken_at.isoformat(),
        },
    )
    assert record_response.status_code == 201
    record = record_response.json()

    item = next(
        item
        for item in client.get("/api/today", params={"date": day}).json()["items"]
        if item["reminder_id"] == reminder["id"]
    )
    assert item["status"] == "已服药"
    assert item["record_id"] == record["id"]

    assert client.delete(f"/api/records/{record['id']}").status_code == 204
    assert client.delete(f"/api/reminders/{reminder['id']}").status_code == 204

