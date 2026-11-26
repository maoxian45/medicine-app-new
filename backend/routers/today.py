from datetime import date as Date

from fastapi import APIRouter, HTTPException, Query
from models.today import TodayResponse
from services import today as service

router = APIRouter(prefix='/api/today', tags=['今日状态'])


@router.get('', response_model=TodayResponse, summary='查询今日服药状态')
def get_today_status(
    date: str | None = Query(default=None, description='日期，格式 YYYY-MM-DD')
) -> dict:
    """按日期汇总提醒和服药记录；不传日期取本机当天。

    日期格式不合法时返回 422，与服药记录筛选用例保持一致。
    """

    if date is not None:
        try:
            date = Date.fromisoformat(date).isoformat()
        except ValueError as exc:
            raise HTTPException(
                status_code=422, detail='date 必须使用 YYYY-MM-DD 格式'
            ) from exc
    return service.get_today_status(date)
