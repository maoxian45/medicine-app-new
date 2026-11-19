from fastapi import APIRouter, status
from models.members import MemberCreate, MemberResponse
from services import members as service
router = APIRouter(prefix='/api/members', tags=['家庭成员'])

@router.put('/{member_id}',response_model=MemberResponse)
def update_member(member_id: int,member: MemberCreate):
    return service.update_member(member_id,member)

@router.get('', response_model=list[MemberResponse])
def list_members() -> list[dict]:
    return service.list_members()

@router.get('/{member_id}', response_model=MemberResponse)
def get_member(member_id: int) -> dict:
    return service.get_member(member_id)

@router.post('', response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def create_member(member: MemberCreate) -> dict:
    return service.create_member(member)

@router.delete('/{member_id}', status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int) -> None:
    return service.delete_member(member_id)
