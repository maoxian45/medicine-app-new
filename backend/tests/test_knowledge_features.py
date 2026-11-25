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


def test_edit_rechecks_without_old_medicine_and_preserves_stock_confirmation(client):
    for entry in repo.entries(True):
        repo.change_state(entry['id'], 'approved', 1)
    member = client.post('/api/members', json={'name': '重核对测试'}).json()
    payload = {'name': '旧药', 'owner': member['name'], 'dose': '测试量',
               'frequency': '测试频次', 'confirmed': True, 'ingredients': ['华法林']}
    medicine = client.post('/api/medicines', json=payload).json()
    url = f"/api/medicines/{medicine['id']}"
    assert client.put(url, json={**payload, 'stock': '测试库存'}).json()['confirmed']
    updated = {**payload, 'name': '新药', 'ingredients': ['布洛芬']}
    assert client.put(url, json={**updated, 'confirmed': False}).status_code == 422
    result = client.put(url, json=updated)
    assert result.status_code == 200
    assert result.json()['confirmed']
    assert client.get(url).json()['ingredients'] == ['布洛芬']
    client.post('/api/medicines', json={'name': '另一药', 'owner': member['name'], 'ingredients': ['华法林']})
    owner_changed = client.put(url, json={**updated, 'name': '再核对药品'})
    assert owner_changed.status_code == 409


def test_published_food_and_population_rules_are_matched(client):
    admin = login(client, 'admin')
    member = client.post('/api/members', json={'name': '新规则测试', 'role': '儿童'}).json()
    client.post('/api/medicines', json={'name': '测试药', 'owner': member['name'], 'ingredients': ['测试成分']})
    check = {'member_id': member['id'], 'foods': ['测试饮品']}
    for kind, target in [('food_rule', '测试饮品'), ('population_rule', '儿童')]:
        draft = client.post('/api/admin/knowledge', headers=admin, json={
            'name': kind, 'kind': kind, 'left': '测试成分', 'right': target,
            'impact': '测试提示', 'source_name': '测试来源', 'source_url': 'https://example.com',
            'chapter': '测试章节', 'source_version': '1', 'original': '测试内容'
        })
        assert draft.status_code == 201
        entry_id = draft.json()['id']
        before = client.post('/api/interactions/check', json=check).json()
        assert all(item['id'] != entry_id for item in before['items'])
        assert client.post(f'/api/admin/knowledge/{entry_id}/approve', headers=admin).status_code == 200
    report = client.post('/api/interactions/check', json=check).json()
    assert {item['kind'] for item in report['items']} == {'food_rule', 'population_rule'}
    report = client.post('/api/interactions/check', json={**check, 'foods': ['其他饮品']}).json()
    assert {item['kind'] for item in report['items']} == {'population_rule'}


def test_manual_record_stores_actual_time_separately(client):
    payload = {'medicine_name': '测试药', 'member_name': '测试儿童', 'taken_at': '2020-01-02T12:30:00+08:00'}
    response = client.post('/api/records', json=payload)
    assert response.status_code == 201
    row = response.json()
    assert row['taken_at'] == '2020-01-02T04:30:00+00:00'
    assert row['created_at'] != row['taken_at']
    assert client.get('/api/records', params={'date': '2020-01-02'}).json()[0]['id'] == row['id']
    assert client.post('/api/records', json={**payload, 'taken_at': '2099-01-01T00:00:00Z'}).status_code == 422
