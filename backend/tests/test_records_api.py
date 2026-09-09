"""服药记录撤销接口自动化测试。"""

from uuid import uuid4

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

    day = record["taken_at"][:10]
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
