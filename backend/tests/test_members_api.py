"""家庭成员接口自动化测试。"""

from uuid import uuid4

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_delete_member_removes_only_target_member() -> None:
    """创建测试成员后应能按其 ID 删除，随后读取应返回 404。"""

    member_name = f"删除测试成员-{uuid4().hex[:8]}"
    create_response = client.post(
        "/api/members",
        json={"name": member_name},
    )
    assert create_response.status_code == 201
    member_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/members/{member_id}")
    assert delete_response.status_code == 204
    assert delete_response.content == b""

    get_response = client.get(f"/api/members/{member_id}")
    assert get_response.status_code == 404


def test_delete_unknown_member_returns_404() -> None:
    """不存在的成员不能静默删除。"""

    response = client.delete("/api/members/999999")
    assert response.status_code == 404
