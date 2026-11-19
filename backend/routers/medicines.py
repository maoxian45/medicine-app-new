from fastapi import APIRouter, Query, status
from models.medicines import MedicineFields, MedicineCreate, MedicineUpdate, MedicineResponse
from services import medicines as service
router = APIRouter(prefix='/api/medicines', tags=['药品'])

@router.get('', response_model=list[MedicineResponse])
def list_medicines(owner: str | None=Query(default=None, description='按家庭成员名称筛选')) -> list[dict]:
    return service.list_medicines(owner)

@router.get('/{medicine_id}', response_model=MedicineResponse)
def get_medicine(medicine_id: int) -> dict:
    return service.get_medicine(medicine_id)

@router.post('', response_model=MedicineResponse, status_code=status.HTTP_201_CREATED)
def create_medicine(medicine: MedicineCreate) -> dict:
    return service.create_medicine(medicine)

@router.put('/{medicine_id}', response_model=MedicineResponse)
def update_medicine(medicine_id: int, medicine: MedicineUpdate) -> dict:
    return service.update_medicine(medicine_id, medicine)

@router.delete('/{medicine_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_medicine(medicine_id: int) -> None:
    return service.delete_medicine(medicine_id)
from services.medicines import _resolve_date_fields
