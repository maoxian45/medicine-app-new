from repositories import members as repository
from models.members import MemberCreate
import sqlite3
from fastapi import HTTPException

def list_members() -> list[dict]:
    rows, = repository.list_members_transaction()
    return [dict(row) for row in rows]

def get_member(member_id: int) -> dict:
    row, = repository.get_member_transaction(member_id)
    if row is None:
        raise HTTPException(status_code=404, detail='家庭成员不存在')
    return dict(row)

def create_member(member: MemberCreate) -> dict:
    try:
        row, = repository.create_member_transaction(member)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail='成员名称已存在') from exc
    return dict(row)

def delete_member(member_id: int) -> None:
    """删除一名家庭成员；不存在时返回 404，避免误以为删除成功。"""
    cursor, = repository.delete_member_transaction(member_id)
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail='家庭成员不存在')


def update_member(member_id,member):
    try: result=repository.update_member_transaction(member_id,member)
    except sqlite3.IntegrityError: raise HTTPException(409,'成员名称已存在')
    if result is None: raise HTTPException(404,'家庭成员不存在')
    return result
