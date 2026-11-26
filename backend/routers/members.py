from fastapi import APIRouter, status

from models.members import MemberCreate, MemberResponse
from services import members as service

router = APIRouter(prefix='/api/members', tags=['家庭成员'])


@router.get('', response_model=list[MemberResponse], summary='查询成员列表')
def list_members() -> list[dict]:
    return service.list_members()


@router.get('/{member_id}', response_model=MemberResponse, summary='查询单个成员')
def get_member(member_id: int) -> dict:
    """成员不存在时返回 404。"""

    return service.get_member(member_id)


@router.post(
    '',
    response_model=MemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary='新增成员',
)
def create_member(member: MemberCreate) -> dict:
    """成员名称重复时返回 409。"""

    return service.create_member(member)


@router.put('/{member_id}', response_model=MemberResponse, summary='编辑成员')
def update_member(member_id: int, member: MemberCreate):
    """传完整成员字段；改名会同步药箱 owner 和提醒对象，重名返回 409。"""

    return service.update_member(member_id, member)


@router.delete(
    '/{member_id}',
    status_code=status.HTTP_204_NO_CONTENT,
    summary='删除成员',
)
def delete_member(member_id: int) -> None:
    """成员不存在时返回 404。"""

    return service.delete_member(member_id)
