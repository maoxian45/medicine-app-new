from fastapi import APIRouter, Depends, Header
from models.knowledge import KnowledgeEntry, LoginRequest, ChatRequest, AIConfig, RiskCheck, Feedback
from services import knowledge as service, auth, ai
from repositories import knowledge as repo

auth_router=APIRouter(prefix='/api/auth',tags=['登录'])
router=APIRouter(prefix='/api',tags=['知识与AI'],dependencies=[Depends(auth.require_family)])
admin_router=APIRouter(prefix='/api/admin',tags=['知识管理'],dependencies=[Depends(auth.require_admin)])


@auth_router.post('/login')
def login(request: LoginRequest):
    return auth.login(request.username,request.password)


@auth_router.post('/logout')
def logout(authorization: str = Header(default='')):
    repo.revoke(authorization.removeprefix('Bearer '))
    return {'ok':True}


@router.get('/knowledge/drugs')
def search(keyword: str=''):
    return service.search(keyword)


@router.get('/knowledge/drugs/{entry_id}')
def detail(entry_id: int):
    return service.detail(entry_id)


@router.post('/knowledge/feedback',status_code=201)
def feedback(request: Feedback):
    service.detail(request.entry_id)
    repo.feedback(request.entry_id,request.message)
    return {'message':'反馈已保存，待管理员核实；不会直接修改已发布知识。'}


@router.post('/interactions/check')
def check(request: RiskCheck):
    return service.risk_report(request.member_id,request.candidate_name,request.candidate_ingredients,
                               exclude_medicine_id=request.exclude_medicine_id,foods=request.foods)


@router.get('/members/{member_id}/risk-report')
def report(member_id: int):
    return service.risk_report(member_id)


@router.get('/ai/status')
def ai_status():
    return {'configured':ai.status()['configured']}


@router.get('/ai/sessions')
def sessions():
    return repo.chat_sessions()


@router.get('/ai/sessions/{session_id}')
def messages(session_id: int):
    from fastapi import HTTPException
    result=repo.messages(session_id)
    if result is None: raise HTTPException(404,'会话不存在')
    return result


@router.post('/ai/chat')
def chat(request: ChatRequest):
    return ai.chat(request)


@admin_router.get('/knowledge')
def admin_list():
    return repo.entries(True)


@admin_router.post('/knowledge',status_code=201)
def create(request: KnowledgeEntry):
    return service.save(request.model_dump())


@admin_router.put('/knowledge/{entry_id}')
def edit(entry_id: int,request: KnowledgeEntry):
    return service.save(request.model_dump(),entry_id)


@admin_router.post('/knowledge/{entry_id}/{action}')
def change(entry_id: int,action: str):
    return service.change(entry_id,action)


@admin_router.get('/knowledge/{entry_id}/versions')
def versions(entry_id: int):
    service.detail(entry_id,True)
    return repo.history(entry_id)


@admin_router.get('/feedback')
def feedback_list():
    return repo.feedback_list()


@admin_router.get('/ai/config')
def ai_config():
    return ai.status()


@admin_router.put('/ai/config')
def configure(request: AIConfig):
    return ai.save_config(request)
