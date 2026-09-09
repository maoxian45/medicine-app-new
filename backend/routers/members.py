import sqlite3

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from database import get_connection


router = APIRouter(prefix="/api/members", tags=["家庭成员"])


class MemberCreate(BaseModel):
    emoji: str = "🙂"
    name: str = Field(min_length=1)
    role: str = ""
    status: str = ""
    age: str = ""
    weight: str = ""
    allergy: str = ""


class MemberResponse(MemberCreate):
    id: int
    created_at: str


@router.get("", response_model=list[MemberResponse])
def list_members() -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            "SELECT * FROM members ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int) -> dict:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT * FROM members WHERE id = ?", (member_id,)
        ).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="家庭成员不存在")
    return dict(row)


@router.post("", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def create_member(member: MemberCreate) -> dict:
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO members
                    (emoji, name, role, status, age, weight, allergy, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
                """,
                (
                    member.emoji,
                    member.name,
                    member.role,
                    member.status,
                    member.age,
                    member.weight,
                    member.allergy,
                ),
            )
            row = connection.execute(
                "SELECT * FROM members WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="成员名称已存在") from exc
    return dict(row)


@router.delete("/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_member(member_id: int) -> None:
    """删除一名家庭成员；不存在时返回 404，避免误以为删除成功。"""

    with get_connection() as connection:
        cursor = connection.execute(
            "DELETE FROM members WHERE id = ?", (member_id,)
        )

    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="家庭成员不存在")
