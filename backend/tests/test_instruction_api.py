"""说明书解析 HTTP 接口自动化测试。"""

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def test_list_standard_samples() -> None:
    """样例列表接口应返回五套标准样例。"""

    response = client.get(
        "/api/instruction/samples"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 5

    sample_ids = {
        item["id"]
        for item in data
    }

    assert sample_ids == {
        "demo_ibuprofen_capsule",
        "demo_paracetamol_tablet",
        "demo_amoxicillin_capsule",
        "demo_nifedipine_sr_tablet",
        "demo_children_fever_medicine",
    }


def test_parse_using_sample_id() -> None:
    """应支持通过 sample_id 生成卡片。"""

    response = client.post(
        "/api/instruction/parse",
        json={
            "sample_id": "demo_nifedipine_sr_tablet",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "硝苯地平缓释片"
    assert data["data_source"] == "sample"
    assert data["sample_id"] == (
        "demo_nifedipine_sr_tablet"
    )
    assert data["expiry_text"]
    assert data["elder_speech_text"]


def test_parse_using_ocr_text() -> None:
    """应支持通过 OCR 原文解析卡片。"""

    response = client.post(
        "/api/instruction/parse",
        json={
            "ocr_text": (
                "维生素C片\n"
                "规格：100mg\n"
                "用法用量：口服，一次1片，"
                "每日1次，饭后服用。\n"
                "有效期：36个月。"
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "维生素C片"
    assert data["expiry"] == "36个月"
    assert data["expiry_text"] == "有效期：36个月"
    assert data["elder_speech_text"]


def test_reject_both_inputs() -> None:
    """ocr_text 和 sample_id 不能同时提交。"""

    response = client.post(
        "/api/instruction/parse",
        json={
            "ocr_text": "布洛芬缓释胶囊",
            "sample_id": "demo_ibuprofen_capsule",
        },
    )

    assert response.status_code == 400


def test_reject_empty_inputs() -> None:
    """两个输入都为空时应返回 400。"""

    response = client.post(
        "/api/instruction/parse",
        json={},
    )

    assert response.status_code == 400


def test_unknown_sample_returns_404() -> None:
    """不存在的样例 ID 应返回 404。"""

    response = client.post(
        "/api/instruction/parse",
        json={
            "sample_id": "not-exist",
        },
    )

    assert response.status_code == 404