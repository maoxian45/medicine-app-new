from fastapi import APIRouter, Query, status
from models.medicines import MedicineCreate, MedicineResponse, MedicineUpdate
from services import medicines as service

router = APIRouter(prefix='/api/medicines', tags=['药品'])


@router.get('', response_model=list[MedicineResponse], summary='查询药箱药品')
def list_medicines(
    owner: str | None = Query(default=None, description='按家庭成员名称筛选')
) -> list[dict]:
    """按成员名称筛选药箱；不传 owner 返回全部药品。"""

    return service.list_medicines(owner)


@router.get('/{medicine_id}', response_model=MedicineResponse, summary='查询单个药品')
def get_medicine(medicine_id: int) -> dict:
    """药品不存在时返回 404。"""

    return service.get_medicine(medicine_id)


@router.post(
    '',
    response_model=MedicineResponse,
    status_code=status.HTTP_201_CREATED,
    summary='新增药品',
)
def create_medicine(medicine: MedicineCreate) -> dict:
    """已核对（confirmed=true）时先校验必填项与组合风险。

    缺药名、成分、使用者、用量或频次返回 422；命中风险且未传
    risk_accepted 返回 409。
    """

    return service.create_medicine(medicine)


@router.put('/{medicine_id}', response_model=MedicineResponse, summary='编辑药品')
def update_medicine(medicine_id: int, medicine: MedicineUpdate) -> dict:
    """全量替换：请求体必须带完整药品对象，不能只传改动字段。

    改动药名、使用者、成分、用量、频次、用法或规格会要求重新核对（422），
    命中风险需传 risk_accepted（409），并停用该药品关联的提醒；只改库存、
    位置或备注时保留原核对状态。
    """

    return service.update_medicine(medicine_id, medicine)


@router.delete(
    '/{medicine_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='删除药品',
)
def delete_medicine(medicine_id: int) -> None:
    """删除药品并停用其关联提醒；药品不存在时返回 404。"""

    return service.delete_medicine(medicine_id)
