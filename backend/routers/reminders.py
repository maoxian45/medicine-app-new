from fastapi import APIRouter, status
from models.reminders import ReminderCreate, ReminderResponse
from services import reminders as service
from models.reminders import ReminderState

router = APIRouter(prefix='/api/reminders', tags=['提醒计划'])

@router.patch('/{reminder_id}')
def set_state(reminder_id: int,state: ReminderState):
    return service.set_state(reminder_id,state.is_active)

@router.get('', response_model=list[ReminderResponse])
def list_reminders(include_inactive: bool=False) -> list[dict]:
    return service.list_reminders(include_inactive)

@router.get('/{reminder_id}', response_model=ReminderResponse)
def get_reminder(reminder_id: int) -> dict:
    return service.get_reminder(reminder_id)

@router.post('', response_model=ReminderResponse, status_code=status.HTTP_201_CREATED)
def create_reminder(reminder: ReminderCreate) -> dict:
    return service.create_reminder(reminder)

@router.delete('/{reminder_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_reminder(reminder_id: int) -> None:
    return service.delete_reminder(reminder_id)
