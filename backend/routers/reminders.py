from fastapi import APIRouter, status

from models.reminders import ReminderCreate, ReminderResponse, ReminderState
from services import reminders as service

router = APIRouter(prefix='/api/reminders', tags=['提醒计划'])


@router.patch('/{reminder_id}', summary='停用或恢复提醒')
def set_state(reminder_id: int, state: ReminderState):
    """只改启用状态，历史服药记录不受影响。"""

    return service.set_state(reminder_id, state.is_active)


@router.get('', response_model=list[ReminderResponse], summary='查询提醒列表')
def list_reminders(include_inactive: bool = False) -> list[dict]:
    """默认只返回启用中的提醒；传 include_inactive=true 可同时看到已停用。"""

    return service.list_reminders(include_inactive)


@router.get('/{reminder_id}', response_model=ReminderResponse, summary='查询单个提醒')
def get_reminder(reminder_id: int) -> dict:
    """提醒不存在时返回 404。"""

    return service.get_reminder(reminder_id)


@router.post(
    '',
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
    summary='新增提醒',
)
def create_reminder(reminder: ReminderCreate) -> dict:
    """提醒必须绑定具体成员：成员不存在返回 404，传“全部人”返回 422。"""

    return service.create_reminder(reminder)


@router.delete(
    '/{reminder_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='删除提醒',
)
def delete_reminder(reminder_id: int) -> None:
    """没有历史记录时直接删除，有记录时改为停用并保留历史。"""

    return service.delete_reminder(reminder_id)
