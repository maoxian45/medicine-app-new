from fastapi import APIRouter, Depends, Header, HTTPException

from models.knowledge import (
    AIConfig,
    ChatRequest,
    Feedback,
    KnowledgeEntry,
    LoginRequest,
    RiskCheck,
)
from repositories import knowledge as repo
from services import ai, auth
from services import knowledge as service

auth_router = APIRouter(prefix='/api/auth', tags=['登录'])
router = APIRouter(
    prefix='/api',
    tags=['知识与AI'],
    dependencies=[Depends(auth.require_family)],
)
admin_router = APIRouter(
    prefix='/api/admin',
    tags=['知识管理'],
    dependencies=[Depends(auth.require_admin)],
)


@auth_router.post('/login', summary='登录')
def login(request: LoginRequest):
    """家庭端与管理端共用入口，返回 8 小时有效的令牌和角色。"""

    return auth.login(request.username, request.password)


@auth_router.post('/logout', summary='退出登录')
def logout(authorization: str = Header(default='')):
    """注销当前令牌；重复注销不报错。"""

    repo.revoke(authorization.removeprefix('Bearer '))
    return {'ok': True}


@router.get('/knowledge/drugs', summary='检索已发布药品知识')
def search(keyword: str = ''):
    """只返回已审核发布的药品知识，草稿和停用条目不可见。"""

    return service.search(keyword)


@router.get('/knowledge/drugs/{entry_id}', summary='查看药品知识详情')
def detail(entry_id: int):
    """未发布或不存在的条目统一返回 404。"""

    return service.detail(entry_id)


@router.post('/knowledge/feedback', status_code=201, summary='提交纠错反馈')
def feedback(request: Feedback):
    """反馈只登记待核实，不直接修改已发布知识。"""

    service.detail(request.entry_id)
    repo.feedback(request.entry_id, request.message)
    return {'message': '反馈已保存，待管理员核实；不会直接修改已发布知识。'}


@router.post('/interactions/check', summary='入箱或编辑前的风险检查')
def check(request: RiskCheck):
    """按成员药箱、候选药品成分、食物饮品和成员角色计算风险。

    exclude_medicine_id 用于编辑时排除药品自身，避免和自己比对。
    """

    return service.risk_report(
        request.member_id,
        request.candidate_name,
        request.candidate_ingredients,
        exclude_medicine_id=request.exclude_medicine_id,
        foods=request.foods,
    )


@router.get('/members/{member_id}/risk-report', summary='成员药箱风险报告')
def report(member_id: int):
    """成员不存在时返回 404。"""

    return service.risk_report(member_id)


@router.get('/ai/status', summary='查看 AI 是否已配置')
def ai_status():
    return {'configured': ai.status()['configured']}


@router.get('/ai/sessions', summary='查询 AI 会话列表')
def sessions():
    return repo.chat_sessions()


@router.get('/ai/sessions/{session_id}', summary='查询单个会话的消息')
def messages(session_id: int):
    result = repo.messages(session_id)
    if result is None:
        raise HTTPException(404, '会话不存在')
    return result


@router.post('/ai/chat', summary='提问用药知识')
def chat(request: ChatRequest):
    """未收录资料返回 status=insufficient，未配置模型返回 503。"""

    return ai.chat(request)


@admin_router.get('/knowledge', summary='管理端知识列表（含草稿）')
def admin_list():
    return repo.entries(True)


@admin_router.post('/knowledge', status_code=201, summary='新增知识草稿')
def create(request: KnowledgeEntry):
    """kind 取 drug、rule、food_rule 或 population_rule，规则类需填 left/right/impact。"""

    return service.save(request.model_dump())


@admin_router.put('/knowledge/{entry_id}', summary='修改知识条目')
def edit(entry_id: int, request: KnowledgeEntry):
    """修改已发布内容会退回草稿，需要重新审核。"""

    return service.save(request.model_dump(), entry_id)


@admin_router.post('/knowledge/{entry_id}/{action}', summary='审核发布或停用知识')
def change(entry_id: int, action: str):
    """action 只支持 approve、disable。"""

    return service.change(entry_id, action)


@admin_router.get('/knowledge/{entry_id}/versions', summary='查询知识版本历史')
def versions(entry_id: int):
    service.detail(entry_id, True)
    return repo.history(entry_id)


@admin_router.get('/feedback', summary='查询纠错反馈')
def feedback_list():
    return repo.feedback_list()


@admin_router.get('/ai/config', summary='查看 AI 配置（不含密钥）')
def ai_config():
    return ai.status()


@admin_router.put('/ai/config', summary='保存 AI 配置')
def configure(request: AIConfig):
    """只接受 HTTPS 服务地址；密钥留空表示保留原值。"""

    return ai.save_config(request)
