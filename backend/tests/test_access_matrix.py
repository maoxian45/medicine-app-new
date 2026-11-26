"""接口权限矩阵：家庭端与管理端令牌不能互相访问。

用例名统一以 test_access_ 开头，以便 tests/conftest.py 跳过登录依赖的
override，让这些用例走真实的令牌校验。
"""

import re

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

PUBLIC_PATHS = {"/api/health", "/api/auth/login", "/api/auth/logout"}
ADMIN_PREFIX = "/api/admin"
HTTP_METHODS = {"get", "post", "put", "patch", "delete"}


def _concrete(path: str) -> str:
    """把路径参数替换成固定值，便于直接请求。"""

    return re.sub(r"\{[^}]+\}", "1", path)


def _endpoints(family: bool) -> list[tuple[str, str]]:
    """从 OpenAPI 枚举家庭端或管理端的 (方法, 路径)，跳过公开接口。

    FastAPI 0.165 起 app.routes 把 include_router 的路由包成 _IncludedRouter，
    直接遍历拿不到具体接口，因此统一从 OpenAPI 文档读取，结果也更稳定。
    """

    endpoints: set[tuple[str, str]] = set()
    for path, operations in app.openapi()["paths"].items():
        if not path.startswith("/api/") or path in PUBLIC_PATHS:
            continue
        if path.startswith(ADMIN_PREFIX) == family:
            continue
        endpoints.update(
            (method.upper(), _concrete(path))
            for method in operations
            if method.lower() in HTTP_METHODS
        )
    return sorted(endpoints)


FAMILY_ENDPOINTS = _endpoints(family=True)
ADMIN_ENDPOINTS = _endpoints(family=False)


def _token(username: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": username, "password": f"{username}-demo"},
    )
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["token"]}


def _call(method: str, path: str, headers: dict[str, str]):
    return client.request(method, path, headers=headers)


def test_access_matrix_covers_all_business_endpoints() -> None:
    """权限矩阵要覆盖到实际接口，避免路由新增或删除后无人检查。

    接口有增减时同步修改下面的数字，让矩阵和实际路由保持一致。
    """

    assert len(FAMILY_ENDPOINTS) == 30
    assert len(ADMIN_ENDPOINTS) == 8
    assert ("GET", "/api/health") not in FAMILY_ENDPOINTS


def test_access_health_check_is_public() -> None:
    """健康检查不校验令牌，用于启动和联调前的连通性检查。"""

    assert client.get("/api/health").status_code == 200


@pytest.mark.parametrize("method,path", FAMILY_ENDPOINTS)
def test_access_family_api_requires_family_token(method, path) -> None:
    """家庭端接口：无令牌 401，管理员令牌 403。"""

    assert _call(method, path, {}).status_code == 401
    assert _call(method, path, _token("admin")).status_code == 403


@pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
def test_access_admin_api_requires_admin_token(method, path) -> None:
    """管理端接口：无令牌 401，家庭令牌 403。"""

    assert _call(method, path, {}).status_code == 401
    assert _call(method, path, _token("family")).status_code == 403


@pytest.mark.parametrize(
    "method,path", [item for item in FAMILY_ENDPOINTS if item[0] == "GET"]
)
def test_access_family_token_can_read(method, path) -> None:
    """家庭令牌可以进入家庭端只读接口，具体业务状态不限。"""

    assert _call(method, path, _token("family")).status_code not in (401, 403)
