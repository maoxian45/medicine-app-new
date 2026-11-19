"""Local coursework accounts with separate roles; no admin access to family APIs."""
import os
import secrets
import time
from fastapi import Header, HTTPException
from repositories import knowledge as repo


def login(username, password):
    accounts={'family': ('family',os.getenv('FAMILY_PASSWORD','family-demo')),
              'admin': ('admin',os.getenv('ADMIN_PASSWORD','admin-demo'))}
    account=accounts.get(username)
    if not account or not secrets.compare_digest(password,account[1]):
        raise HTTPException(401,'账号或密码错误')
    token=secrets.token_urlsafe(32)
    repo.add_token(token,account[0],time.time()+8*3600)
    return {'token':token,'role':account[0]}


def role(authorization: str = Header(default='')):
    token=authorization.removeprefix('Bearer ')
    result=repo.token_role(token,time.time())
    if not result: raise HTTPException(401,'请登录或重新登录')
    return result


def require_family(authorization: str = Header(default='')):
    if role(authorization)!='family': raise HTTPException(403,'知识库管理员无权访问家庭数据')


def require_admin(authorization: str = Header(default='')):
    if role(authorization)!='admin': raise HTTPException(403,'仅知识库管理员可执行此操作')
