import pytest
from fastapi.testclient import TestClient
import database
from main import app
from repositories import knowledge as repo
from services import ai


@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(database,'DATA_DIR',tmp_path)
    monkeypatch.setattr(database,'DATABASE_PATH',tmp_path/'features.db')
    with TestClient(app) as c:
        yield c


def login(client,role):
    response=client.post('/api/auth/login',json={'username':role,'password':role+'-demo'})
    assert response.status_code==200
    return {'Authorization':'Bearer '+response.json()['token']}


def test_access_role_isolation(client):
    family=login(client,'family')
    admin=login(client,'admin')
    assert client.get('/api/members').status_code==401
    assert client.get('/api/members',headers=admin).status_code==403
    assert client.get('/api/admin/knowledge',headers=family).status_code==403
    assert client.get('/api/members',headers=family).status_code==200
    client.post('/api/auth/logout',headers=admin)
    assert client.get('/api/admin/knowledge',headers=admin).status_code==401


def test_knowledge_review_history_disable_and_risk(client):
    admin=login(client,'admin')
    assert client.get('/api/knowledge/drugs').json()==[]
    drafts=client.get('/api/admin/knowledge',headers=admin).json()
    for e in drafts:
        assert client.post(f"/api/admin/knowledge/{e['id']}/approve",headers=admin).status_code==200
    drugs=client.get('/api/knowledge/drugs',params={'keyword':'布洛芬'}).json()
    assert drugs[0]['ingredients']==['布洛芬']
    member=client.post('/api/members',json={'name':'规则测试'}).json()
    client.post('/api/medicines',json={'name':'华法林钠片','owner':member['name']})
    report=client.post('/api/interactions/check',json={'member_id':member['id'],'candidate_name':'布洛芬缓释胶囊'}).json()
    assert report['count']==1
    by_ingredient=client.post('/api/interactions/check',json={
        'member_id':member['id'],'candidate_name':'待匹配商品名','candidate_ingredients':['布洛芬']}).json()
    assert by_ingredient['count']==1
    rule=next(e for e in drafts if e['kind']=='rule')
    client.post(f"/api/admin/knowledge/{rule['id']}/disable",headers=admin)
    assert client.post('/api/interactions/check',json={'member_id':member['id'],'candidate_name':'布洛芬缓释胶囊'}).json()['count']==0
    versions=client.get(f"/api/admin/knowledge/{rule['id']}/versions",headers=admin).json()
    assert len(versions)==3
    assert versions[-1]['snapshot']['review_status']=='draft'


def test_knowledge_requires_source_and_version(client):
    admin=login(client,'admin')
    assert client.post('/api/admin/knowledge',headers=admin,json={'name':'缺少来源'}).status_code==422


def test_ai_unconfigured_insufficient_and_history(client,monkeypatch):
    monkeypatch.setattr(ai,'config',lambda:{'base_url':'','model':'','api_key':''})
    response=client.post('/api/ai/chat',json={'question':'未收录的药品知识'})
    assert response.json()['status']=='insufficient'
    session_id=response.json()['session_id']
    assert len(client.get(f'/api/ai/sessions/{session_id}').json())==2
    for e in repo.entries(True): repo.change_state(e['id'],'approved',1)
    assert client.post('/api/ai/chat',json={'question':'布洛芬注意事项'}).status_code==503
    assert client.post('/api/ai/chat',json={'question':'帮我停药'}).json()['status']=='out_of_scope'


def test_confirmed_medicine_requires_fields_and_risk_ack(client):
    for e in repo.entries(True): repo.change_state(e['id'],'approved',1)
    member=client.post('/api/members',json={'name':'核对测试'}).json()
    client.post('/api/medicines',json={'name':'华法林','owner':member['name']})
    body={'name':'布洛芬','owner':member['name'],'confirmed':True,'dose':'按已核对说明','frequency':'按已核对说明','ingredients':['布洛芬']}
    assert client.post('/api/medicines',json=body).status_code==409
    body['risk_accepted']=True
    response=client.post('/api/medicines',json=body)
    assert response.status_code==201
    assert response.json()['confirmed'] is True


def test_ai_multi_turn_uses_context_and_attaches_sources(client,monkeypatch):
    for e in repo.entries(True): repo.change_state(e['id'],'approved',1)
    monkeypatch.setattr(ai,'config',lambda:{'base_url':'https://example.org/v1','model':'test-model','api_key':'test-only'})
    requests=[]
    class Response:
        def raise_for_status(self): pass
        def json(self): return {'choices':[{'message':{'content':'测试响应：请核对所提供的知识资料。'}}]}
    class Client:
        def __init__(self,**kwargs): pass
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def post(self,url,**kwargs):
            requests.append(kwargs['json'])
            return Response()
    monkeypatch.setattr(ai.httpx,'Client',Client)
    first=client.post('/api/ai/chat',json={'question':'布洛芬注意事项'}).json()
    assert first['status']=='answered'
    assert first['sources'][0]['source_url'].startswith('https://medlineplus.gov/')
    second=client.post('/api/ai/chat',json={'question':'还有哪些注意事项？','session_id':first['session_id']}).json()
    assert second['session_id']==first['session_id']
    assert any(m['content']=='布洛芬注意事项' for m in requests[1]['messages'])
    assert len(repo.messages(first['session_id']))==4


def test_reminder_state_and_member_edit(client):
    member=client.post('/api/members',json={'name':'提醒测试成员'}).json()
    assert client.put(f"/api/members/{member['id']}",json={'name':'修改后成员','weight':'60kg'}).status_code==200
    medicine=client.post('/api/medicines',json={'name':'提醒测试药','owner':'修改后成员'}).json()
    reminder=client.post('/api/reminders',json={'medicine_id':medicine['id'],'medicine_name':medicine['name'],'member_name':'修改后成员','time':'08:00'}).json()
    assert client.patch(f"/api/reminders/{reminder['id']}",json={'is_active':False}).status_code==200
    assert client.get('/api/today').json()['total']==0
    assert client.patch(f"/api/reminders/{reminder['id']}",json={'is_active':True}).status_code==200
    assert client.get('/api/today').json()['total']==1
