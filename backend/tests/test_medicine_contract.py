"""药品业务接口字段约定测试。"""

import sqlite3
from uuid import uuid4

from fastapi.testclient import TestClient

from database import _migrate_medicines_schema, init_db
from main import app
from routers.medicines import MedicineCreate, _resolve_date_fields


client = TestClient(app)


def test_medicine_payload_uses_all_date_fields() -> None:
    """药品保存模型应包含生产日期、保质期和具体有效期。"""

    payload = MedicineCreate(
        name="测试药品",
        production_date="2024-01-31",
        shelf_life="36个月",
        expiry_date="2027-12",
    )

    assert payload.model_dump()["production_date"] == "2024-01-31"
    assert payload.model_dump()["shelf_life"] == "36个月"
    assert payload.model_dump()["expiry_date"] == "2027-12"
    assert "expiry" not in payload.model_dump()


def test_medicine_openapi_uses_expiry_date() -> None:
    """Swagger 的药品请求和响应字段应与前端契约一致。"""

    schemas = app.openapi()["components"]["schemas"]

    for schema_name in ("MedicineCreate", "MedicineUpdate", "MedicineResponse"):
        properties = schemas[schema_name]["properties"]
        assert {"production_date", "shelf_life", "expiry_date"} <= properties.keys()
        assert "expiry" not in properties


def test_date_fields_default_and_calculate_expiry_date() -> None:
    """未填生产日期默认保质期；填写后按自然月计算具体有效期。"""

    assert _resolve_date_fields("", "", "") == ("", "36个月", "")
    assert _resolve_date_fields("2024-01-31", "1个月", "") == (
        "2024-01-31",
        "1个月",
        "2024-02-29",
    )


def test_migration_moves_legacy_shelf_life_out_of_expiry_date() -> None:
    """旧数据的 expiry_date='36个月' 应迁移为 shelf_life。"""

    connection = sqlite3.connect(":memory:")
    connection.execute(
        "CREATE TABLE medicines (id INTEGER PRIMARY KEY, expiry_date TEXT NOT NULL)"
    )
    connection.execute(
        "INSERT INTO medicines (expiry_date) VALUES ('36个月'), ('2027-12-01')"
    )

    _migrate_medicines_schema(connection)
    rows = connection.execute(
        "SELECT production_date, shelf_life, expiry_date FROM medicines ORDER BY id"
    ).fetchall()
    connection.close()

    assert rows == [
        ("", "36个月", ""),
        ("", "36个月", "2027-12-01"),
    ]


def test_create_medicine_calculates_and_returns_expiry_date() -> None:
    """药品新增接口应保存三项日期字段，并返回计算后的有效期。"""

    init_db()
    response = client.post(
        "/api/medicines",
        json={
            "name": f"日期测试药-{uuid4().hex[:8]}",
            "production_date": "2024-01-31",
            "shelf_life": "1个月",
        },
    )
    assert response.status_code == 201
    medicine = response.json()
    assert medicine["production_date"] == "2024-01-31"
    assert medicine["shelf_life"] == "1个月"
    assert medicine["expiry_date"] == "2024-02-29"

    assert client.delete(f"/api/medicines/{medicine['id']}").status_code == 204


def test_delete_medicine_deactivates_only_id_linked_reminders() -> None:
    """删除药品只能停用绑定相同 medicine_id 的提醒，不能按药名误伤。"""

    init_db()
    shared_name = f"同名关联测试药-{uuid4().hex[:8]}"
    medicine_a_response = client.post("/api/medicines", json={"name": shared_name})
    medicine_b_response = client.post("/api/medicines", json={"name": shared_name})
    assert medicine_a_response.status_code == 201
    assert medicine_b_response.status_code == 201
    medicine_a_id = medicine_a_response.json()["id"]
    medicine_b_id = medicine_b_response.json()["id"]

    linked_a = client.post(
        "/api/reminders",
        json={
            "medicine_id": medicine_a_id,
            "medicine_name": shared_name,
            "member_name": "我",
            "time": "08:10",
        },
    )
    linked_b = client.post(
        "/api/reminders",
        json={
            "medicine_id": medicine_b_id,
            "medicine_name": shared_name,
            "member_name": "我",
            "time": "08:20",
        },
    )
    legacy_same_name = client.post(
        "/api/reminders",
        json={
            "medicine_name": shared_name,
            "member_name": "我",
            "time": "08:30",
        },
    )
    assert linked_a.status_code == linked_b.status_code == legacy_same_name.status_code == 201

    assert client.delete(f"/api/medicines/{medicine_a_id}").status_code == 204
    assert client.get(f"/api/medicines/{medicine_a_id}").status_code == 404

    active_ids = {item["id"] for item in client.get("/api/reminders").json()}
    assert linked_a.json()["id"] not in active_ids
    assert linked_b.json()["id"] in active_ids
    assert legacy_same_name.json()["id"] in active_ids

    all_reminders = {
        item["id"]: item
        for item in client.get("/api/reminders?include_inactive=true").json()
    }
    assert all_reminders[linked_a.json()["id"]]["is_active"] is False

    assert client.delete(f"/api/reminders/{linked_b.json()['id']}").status_code == 204
    assert client.delete(f"/api/reminders/{legacy_same_name.json()['id']}").status_code == 204
    assert client.delete(f"/api/medicines/{medicine_b_id}").status_code == 204
