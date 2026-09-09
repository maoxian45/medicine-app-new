"""提醒计划接口自动化测试。"""

from uuid import uuid4

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def _create_reminder() -> dict:
    response = client.post(
        "/api/reminders",
        json={
            "medicine_name": f"删除测试药品-{uuid4().hex[:8]}",
            "member_name": "我",
            "time": "09:00",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_delete_reminder_removes_unrecorded_reminder() -> None:
    """没有服药记录的提醒可以直接删除。"""

    reminder = _create_reminder()
    reminder_id = reminder["id"]

    response = client.delete(f"/api/reminders/{reminder_id}")
    assert response.status_code == 204
    assert client.get(f"/api/reminders/{reminder_id}").status_code == 404


def test_delete_unknown_reminder_returns_404() -> None:
    """不存在的提醒不能静默删除。"""

    response = client.delete("/api/reminders/999999")
    assert response.status_code == 404


def test_delete_reminder_with_record_deactivates_and_preserves_history() -> None:
    """已服药提醒删除后不再显示，但服药历史必须保留。"""

    reminder = _create_reminder()
    reminder_id = reminder["id"]
    record_response = client.post(
        "/api/records",
        json={
            "reminder_id": reminder_id,
            "medicine_name": reminder["medicine_name"],
            "member_name": reminder["member_name"],
        },
    )
    assert record_response.status_code == 201
    record_id = record_response.json()["id"]

    response = client.delete(f"/api/reminders/{reminder_id}")
    assert response.status_code == 204
    assert reminder_id not in {
        item["id"]
        for item in client.get("/api/reminders").json()
    }
    assert reminder_id not in {
        item["reminder_id"]
        for item in client.get("/api/today").json()["items"]
    }
    assert record_id in {
        item["id"]
        for item in client.get("/api/records").json()
    }

    assert client.delete(f"/api/records/{record_id}").status_code == 204


def test_create_reminder_requires_specific_existing_member() -> None:
    """提醒不能绑定全体成员或不存在的成员。"""

    shared_member_response = client.post(
        "/api/reminders",
        json={
            "medicine_name": "成员校验测试药",
            "member_name": "全部人",
            "time": "09:00",
        },
    )
    assert shared_member_response.status_code == 422
    assert "具体家庭成员" in shared_member_response.json()["detail"]

    missing_member_response = client.post(
        "/api/reminders",
        json={
            "medicine_name": "成员校验测试药",
            "member_name": "不存在的成员",
            "time": "09:00",
        },
    )
    assert missing_member_response.status_code == 404
    assert "成员不存在" in missing_member_response.json()["detail"]

    missing_medicine_response = client.post(
        "/api/reminders",
        json={
            "medicine_id": 999999,
            "medicine_name": "成员校验测试药",
            "member_name": "我",
            "time": "09:00",
        },
    )
    assert missing_medicine_response.status_code == 404
    assert "关联药品不存在" in missing_medicine_response.json()["detail"]
