from fastapi import APIRouter, Query
from models.today import TodayItem, TodayResponse
from services import today as service
router = APIRouter(prefix='/api/today', tags=['今日状态'])

@router.get('', response_model=TodayResponse)
def get_today_status(date: str | None=Query(default=None, description='日期，格式 YYYY-MM-DD')) -> dict:
    return service.get_today_status(date)
