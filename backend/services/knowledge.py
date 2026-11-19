"""Knowledge publication and deterministic risk reports. Owner: qhy."""
from fastapi import HTTPException
from repositories import knowledge as repo
from services import members, medicines


def validate(payload):
    if payload['kind']=='rule' and not all(payload[k].strip() for k in ('left','right','impact')):
        raise HTTPException(422,'规则须填写双方成分及可能影响')
    if payload['kind']=='drug' and not payload['ingredients']:
        raise HTTPException(422,'药品知识须填写有效成分')


def search(keyword=''):
    keyword=keyword.strip().lower()
    return [e for e in repo.entries() if e['kind']=='drug' and
            (not keyword or keyword in ' '.join([e['name'],*e['aliases'],*e['ingredients']]).lower())]


def detail(entry_id, admin=False):
    item=repo.entry(entry_id)
    if not item or (not admin and (not item['active'] or item['review_status']!='approved')):
        raise HTTPException(404,'知识条目不存在或尚未发布')
    return item


def save(payload,entry_id=None):
    validate(payload)
    if entry_id is not None: detail(entry_id,True)
    return repo.save(payload,entry_id)


def change(entry_id,action):
    item=detail(entry_id,True)
    if action=='approve':
        validate(item)
        return repo.change_state(entry_id,'approved',1)
    if action=='disable': return repo.change_state(entry_id,'disabled',0)
    raise HTTPException(422,'不支持的操作')


def components(name):
    matches=search(name)
    exact=[e for e in matches if name in [e['name'],*e['aliases'],*e['ingredients']]]
    return set(i for e in exact for i in e['ingredients']) or {name}


def risk_report(member_id,candidate_name='',candidate_ingredients=None):
    member=members.get_member(member_id)
    drugs=[m for m in medicines.list_medicines(member['name']) if m['status'] not in ('停用','已停用')]
    names=[m['name'] for m in drugs]
    ingredient_sets=[set(m.get('ingredients') or components(m['name'])) for m in drugs]
    if candidate_name:
        names.append(candidate_name)
        ingredient_sets.append(set(candidate_ingredients or components(candidate_name)))
    rules=[e for e in repo.entries() if e['kind']=='rule']
    result=[]
    seen=set()
    for i,left in enumerate(names):
        for j,right in enumerate(names[i+1:],i+1):
            for rule in rules:
                a,b=ingredient_sets[i],ingredient_sets[j]
                if ((rule['left'] in a and rule['right'] in b) or (rule['right'] in a and rule['left'] in b)) and rule['id'] not in seen:
                    seen.add(rule['id'])
                    result.append({**rule,'drugs':[left,right]})
    order={'严重风险':0,'需关注':1,'一般提醒':2,'数据不足':3}
    result.sort(key=lambda r:order[r['level']])
    missing=[n for n in names if not search(n)]
    return {'member_id':member_id,'member_name':member['name'],'items':result,'count':len(result),
            'highest_level':result[0]['level'] if result else ('数据不足' if missing else '暂未发现已收录风险'),
            'message':'暂未发现已收录风险' if not result else '请查看风险依据并咨询医生或药师。',
            'missing':missing,'population_notes':[{'drug':n,'text':e['special_population']} for n in names for e in search(n) if e['special_population']]}
