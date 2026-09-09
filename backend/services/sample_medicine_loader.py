"""读取、列出并匹配药品演示样例数据。"""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from typing import Any


SAMPLE_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "sample_data"
    / "sample_medicines.json"
)


@lru_cache(maxsize=1)
def load_sample_medicines() -> list[dict[str, Any]]:
    """从 JSON 文件读取全部样例药品数据。"""

    try:
        with SAMPLE_DATA_PATH.open(
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)
    except FileNotFoundError as exc:
        raise RuntimeError(
            f"未找到样例药品文件：{SAMPLE_DATA_PATH}"
        ) from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "样例药品 JSON 格式错误"
        ) from exc
    except OSError as exc:
        raise RuntimeError(
            "读取样例药品文件失败"
        ) from exc

    medicines = data.get("medicines")

    if not isinstance(medicines, list):
        raise RuntimeError(
            "样例药品文件缺少 medicines 列表"
        )

    return medicines


def _normalize_text(text: str) -> str:
    """清除空白并统一英文字符大小写。"""

    return "".join(
        text.lower().split()
    )


def find_sample_by_id(
    sample_id: str,
) -> dict[str, Any] | None:
    """根据样例 ID 直接读取一套样例药品。"""

    normalized_id = sample_id.strip().lower()

    if not normalized_id:
        return None

    for medicine in load_sample_medicines():
        medicine_id = medicine.get("id")

        if (
            isinstance(medicine_id, str)
            and medicine_id.lower() == normalized_id
        ):
            return deepcopy(medicine)

    return None


def list_sample_summaries() -> list[dict[str, str]]:
    """返回前端样例选择弹窗使用的简要列表。"""

    summaries: list[dict[str, str]] = []

    for medicine in load_sample_medicines():
        summaries.append(
            {
                "id": str(medicine.get("id", "")),
                "name": str(medicine.get("name", "")),
                "emoji": str(medicine.get("emoji", "💊")),
                "category": str(medicine.get("category", "")),
                "expiry_text": str(
                    medicine.get("expiry_text", "")
                ),
            }
        )

    return summaries


def find_best_sample(
    ocr_text: str,
) -> dict[str, Any] | None:
    """根据 OCR 文字查找最匹配的样例药品。"""

    normalized_text = _normalize_text(
        ocr_text
    )

    if not normalized_text:
        return None

    best_sample: dict[str, Any] | None = None
    best_score = 0

    for medicine in load_sample_medicines():
        keywords = medicine.get(
            "match_keywords",
            [],
        )

        if not isinstance(keywords, list):
            continue

        score = 0

        for keyword in keywords:
            if not isinstance(keyword, str):
                continue

            normalized_keyword = _normalize_text(
                keyword
            )

            if (
                normalized_keyword
                and normalized_keyword in normalized_text
            ):
                score += len(normalized_keyword)

        if score > best_score:
            best_score = score
            best_sample = medicine

    if best_sample is None:
        return None

    return deepcopy(best_sample)