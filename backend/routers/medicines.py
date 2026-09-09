import calendar
import json
import re
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from database import get_connection


router = APIRouter(prefix="/api/medicines", tags=["药品"])

DEFAULT_SHELF_LIFE = "36个月"
SHELF_LIFE_PATTERN = re.compile(r"^(\d+)\s*个月$")


class MedicineFields(BaseModel):
    emoji: str = "💊"
    name: str = Field(min_length=1)
    spec: str = ""
    category: str = ""
    owner: str = ""
    dose: str = ""
    frequency: str = ""
    meal_time: str = ""
    method: str = ""
    location: str = ""
    production_date: str = ""
    shelf_life: str = DEFAULT_SHELF_LIFE
    expiry_date: str = ""
    stock: str = ""
    status: str = ""
    risks: list[str] = Field(default_factory=list)
    note: str = ""
    original_text: str = ""


class MedicineCreate(MedicineFields):
    pass


class MedicineUpdate(MedicineFields):
    pass


class MedicineResponse(MedicineFields):
    id: int
    created_at: str


def _medicine_from_row(row: object) -> dict:
    medicine = dict(row)
    try:
        medicine["risks"] = json.loads(medicine["risks"])
    except (TypeError, json.JSONDecodeError):
        medicine["risks"] = []
    return medicine


def _add_months(production_date: date, months: int) -> date:
    """按自然月计算有效期，并处理月末日期。"""

    month_index = production_date.month - 1 + months
    year = production_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(production_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _resolve_date_fields(
    production_date: str,
    shelf_life: str,
    expiry_date: str,
) -> tuple[str, str, str]:
    """标准化日期字段；有生产日期时由保质期计算具体有效期。"""

    normalized_production_date = production_date.strip()
    normalized_shelf_life = shelf_life.strip() or DEFAULT_SHELF_LIFE
    normalized_expiry_date = expiry_date.strip()

    if not normalized_production_date:
        return "", normalized_shelf_life, normalized_expiry_date

    try:
        production_day = date.fromisoformat(normalized_production_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="production_date 必须使用 YYYY-MM-DD 格式",
        ) from exc

    match = SHELF_LIFE_PATTERN.fullmatch(normalized_shelf_life)
    if match is None or int(match.group(1)) <= 0:
        raise HTTPException(
            status_code=422,
            detail="shelf_life 必须使用“36个月”这类格式",
        )

    calculated_expiry_date = _add_months(
        production_day,
        int(match.group(1)),
    ).isoformat()
    return (
        normalized_production_date,
        normalized_shelf_life,
        calculated_expiry_date,
    )


@router.get("", response_model=list[MedicineResponse])
def list_medicines(
    owner: str | None = Query(default=None, description="按家庭成员名称筛选")
) -> list[dict]:
    with get_connection() as connection:
        if owner:
            rows = connection.execute(
                "SELECT * FROM medicines WHERE owner = ? ORDER BY id DESC",
                (owner,),
            ).fetchall()
        else:
            rows = connection.execute(
                "SELECT * FROM medicines ORDER BY id DESC"
            ).fetchall()
    return [_medicine_from_row(row) for row in rows]


@router.get("/{medicine_id}", response_model=MedicineResponse)
def get_medicine(medicine_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM medicines WHERE id = ?", (medicine_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="药品不存在")
    return _medicine_from_row(row)


@router.post("", response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(medicine: MedicineCreate) -> dict:
    production_date, shelf_life, expiry_date = _resolve_date_fields(
        medicine.production_date,
        medicine.shelf_life,
        medicine.expiry_date,
    )
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO medicines
                (emoji, name, spec, category, owner, dose, frequency, meal_time,
                 method, location, production_date, shelf_life, expiry_date,
                 stock, status, risks, note,
                 original_text, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                medicine.emoji,
                medicine.name,
                medicine.spec,
                medicine.category,
                medicine.owner,
                medicine.dose,
                medicine.frequency,
                medicine.meal_time,
                medicine.method,
                medicine.location,
                production_date,
                shelf_life,
                expiry_date,
                medicine.stock,
                medicine.status,
                json.dumps(medicine.risks, ensure_ascii=False),
                medicine.note,
                medicine.original_text,
            ),
        )
        row = connection.execute(
            "SELECT * FROM medicines WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return _medicine_from_row(row)


@router.put("/{medicine_id}", response_model=MedicineResponse)
def update_medicine(medicine_id: int, medicine: MedicineUpdate) -> dict:
    production_date, shelf_life, expiry_date = _resolve_date_fields(
        medicine.production_date,
        medicine.shelf_life,
        medicine.expiry_date,
    )
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT id FROM medicines WHERE id = ?", (medicine_id,)
        ).fetchone()
        if existing is None:
            raise HTTPException(status_code=404, detail="药品不存在")

        connection.execute(
            """
            UPDATE medicines
            SET emoji = ?, name = ?, spec = ?, category = ?, owner = ?,
                dose = ?, frequency = ?, meal_time = ?, method = ?,
                location = ?, production_date = ?, shelf_life = ?,
                expiry_date = ?, stock = ?, status = ?,
                risks = ?, note = ?, original_text = ?
            WHERE id = ?
            """,
            (
                medicine.emoji,
                medicine.name,
                medicine.spec,
                medicine.category,
                medicine.owner,
                medicine.dose,
                medicine.frequency,
                medicine.meal_time,
                medicine.method,
                medicine.location,
                production_date,
                shelf_life,
                expiry_date,
                medicine.stock,
                medicine.status,
                json.dumps(medicine.risks, ensure_ascii=False),
                medicine.note,
                medicine.original_text,
                medicine_id,
            ),
        )
        row = connection.execute(
            "SELECT * FROM medicines WHERE id = ?", (medicine_id,)
        ).fetchone()
    return _medicine_from_row(row)


@router.delete("/{medicine_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_medicine(medicine_id: int) -> None:
    """删除药品，并停用其 ID 关联的仍启用提醒。"""

    with get_connection() as connection:
        medicine = connection.execute(
            "SELECT id FROM medicines WHERE id = ?", (medicine_id,)
        ).fetchone()
        if medicine is None:
            raise HTTPException(status_code=404, detail="药品不存在")

        # 只根据稳定的药品 ID 停用提醒，不能通过药名猜测关联关系。
        connection.execute(
            """
            UPDATE reminders
            SET is_active = 0
            WHERE medicine_id = ? AND is_active = 1
            """,
            (medicine_id,),
        )
        connection.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
