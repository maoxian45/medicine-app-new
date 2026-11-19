from repositories import medicines as repository
from models.medicines import MedicineCreate, MedicineUpdate
import calendar
import json
import re
from datetime import date
from fastapi import HTTPException, Query
DEFAULT_SHELF_LIFE = '36个月'
SHELF_LIFE_PATTERN = re.compile('^(\\d+)\\s*个月$')

def _medicine_from_row(row: object) -> dict:
    medicine = dict(row)
    try:
        medicine['risks'] = json.loads(medicine['risks'])
    except (TypeError, json.JSONDecodeError):
        medicine['risks'] = []
    from repositories.knowledge import confirmed, medicine_ingredients
    medicine['confirmed'] = confirmed(medicine['id'])
    medicine['ingredients'] = medicine_ingredients(medicine['id'])
    return medicine

def _add_months(production_date: date, months: int) -> date:
    """按自然月计算有效期，并处理月末日期。"""
    month_index = production_date.month - 1 + months
    year = production_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(production_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)

def _resolve_date_fields(production_date: str, shelf_life: str, expiry_date: str) -> tuple[str, str, str]:
    """标准化日期字段；有生产日期时由保质期计算具体有效期。"""
    normalized_production_date = production_date.strip()
    normalized_shelf_life = shelf_life.strip() or DEFAULT_SHELF_LIFE
    normalized_expiry_date = expiry_date.strip()
    if not normalized_production_date:
        return ('', normalized_shelf_life, normalized_expiry_date)
    try:
        production_day = date.fromisoformat(normalized_production_date)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail='production_date 必须使用 YYYY-MM-DD 格式') from exc
    match = SHELF_LIFE_PATTERN.fullmatch(normalized_shelf_life)
    if match is None or int(match.group(1)) <= 0:
        raise HTTPException(status_code=422, detail='shelf_life 必须使用“36个月”这类格式')
    calculated_expiry_date = _add_months(production_day, int(match.group(1))).isoformat()
    return (normalized_production_date, normalized_shelf_life, calculated_expiry_date)

def list_medicines(owner: str | None=Query(default=None, description='按家庭成员名称筛选')) -> list[dict]:
    rows, = repository.list_medicines_transaction(owner)
    return [_medicine_from_row(row) for row in rows]

def get_medicine(medicine_id: int) -> dict:
    row, = repository.get_medicine_transaction(medicine_id)
    if row is None:
        raise HTTPException(status_code=404, detail='药品不存在')
    return _medicine_from_row(row)

def create_medicine(medicine: MedicineCreate) -> dict:
    from repositories import knowledge as knowledge_repo
    from services.knowledge import risk_report
    report = None
    if medicine.confirmed:
        if not all((medicine.name.strip(),medicine.owner.strip(),medicine.dose.strip(),medicine.frequency.strip(),medicine.ingredients)):
            raise HTTPException(422,'请核对药名、成分、使用者、用量及频次')
        from services.members import list_members
        member = next((m for m in list_members() if m['name']==medicine.owner),None)
        if member is None: raise HTTPException(404,'使用者不存在')
        report = risk_report(member['id'],medicine.name,medicine.ingredients)
        if report['count'] and not medicine.risk_accepted:
            raise HTTPException(409,'请先查看并确认组合用药风险')
    production_date, shelf_life, expiry_date = _resolve_date_fields(medicine.production_date, medicine.shelf_life, medicine.expiry_date)
    row, = repository.create_medicine_transaction(expiry_date, medicine, production_date, shelf_life)
    knowledge_repo.confirmation(row['id'],medicine.confirmed,medicine.ingredients)
    if report:
        knowledge_repo.save_risk_confirmation(report['member_id'],row['id'],report)
    return _medicine_from_row(row)

def update_medicine(medicine_id: int, medicine: MedicineUpdate) -> dict:
    production_date, shelf_life, expiry_date = _resolve_date_fields(medicine.production_date, medicine.shelf_life, medicine.expiry_date)
    row, = repository.update_medicine_transaction(expiry_date, medicine, medicine_id, production_date, shelf_life)
    from repositories.knowledge import confirmation
    confirmation(medicine_id,False,medicine.ingredients)
    return _medicine_from_row(row)

def delete_medicine(medicine_id: int) -> None:
    """删除药品，并停用其 ID 关联的仍启用提醒。"""
    repository.delete_medicine_transaction(medicine_id)
