<script setup>
import {ref,onMounted,watch,nextTick} from 'vue'
import {api,post} from '../api'
import KnowledgeDetail from '../components/KnowledgeDetail.vue'
const props=defineProps({mode:{type:String,default:'box'}})
const emit=defineEmits(['navigate','ask'])
const members=ref([]),medicines=ref([]),owner=ref(''),error=ref(''),busy=ref(false),message=ref(''),samples=ref([]),sample=ref(''),text=ref(''),ingredients=ref(''),matches=ref([]),report=ref(null),riskAccepted=ref(false),selected=ref(null),summary=ref(null)
const empty=()=>({name:'',spec:'',owner:'',dose:'',frequency:'',method:'',location:'',stock:'',expiry_date:'',original_text:''})
const form=ref(empty()),confirmed=ref(false)
const formElement=ref(null),saveStatus=ref(null),image=ref(null),ocrProgress=ref(''), ocrNotice=ref('')
const detailDialog=ref(null), editDialog=ref(null)
const editing=ref(null), reviewDialog=ref(null), parserError=ref('')
const ingredientStatus=ref(''), resolvingIngredients=ref(false)
let ingredientRequest=0
function expired(medicine){
  const today=new Date().toLocaleDateString('sv-SE')
  return /^\d{4}-\d{2}-\d{2}$/.test(medicine.expiry_date) && medicine.expiry_date<today
}
function outOfStock(medicine){
  return /^0(?:\.0+)?\s*[^\d.]*$/.test(medicine.stock.trim())
}
const ingredientList=()=>ingredients.value.split(/[、,，]/).map(s=>s.trim()).filter(Boolean)
const formValid=()=>formElement.value?.reportValidity() &&
  [form.value.name,form.value.dose,form.value.frequency].every(value=>value.trim()) &&
  ingredientList().length>0

async function prepareImage(file){
  const bitmap=await createImageBitmap(file)
  try{
    // Small leaflet scans benefit from a larger glyph size before segmentation.
    const scale=Math.min(4,1600/bitmap.width,3400/bitmap.height)
    if(scale<=1)return file
    const canvas=document.createElement('canvas')
    canvas.width=Math.round(bitmap.width*scale)
    canvas.height=Math.round(bitmap.height*scale)
    const context=canvas.getContext('2d')
    context.fillStyle='#fff'
    context.fillRect(0,0,canvas.width,canvas.height)
    context.imageSmoothingQuality='high'
    context.drawImage(bitmap,0,0,canvas.width,canvas.height)
    return canvas
  }finally{bitmap.close()}
}

function onImageSelected(event){
  image.value=event.target.files[0] || null
  if(image.value)recognize()
}

async function recognize(){
  if(!image.value || busy.value)return
  busy.value=true
  parserError.value=''
  message.value=''
  ocrNotice.value=''
  ocrProgress.value='正在加载识别组件和语言包…'
  let worker
  try{
    const [{createWorker}, {default: workerPath}]=await Promise.all([
      import('tesseract.js'),
      import('tesseract.js/dist/worker.min.js?url')
    ])
    worker=await createWorker('chi_sim',1,{
      workerPath,
      errorHandler:()=>{},
      logger:({status,progress})=>{
        if(status==='recognizing text')ocrProgress.value=`正在识别 ${Math.round(progress*100)}%`
      }
    })
    const {data}=await worker.recognize(await prepareImage(image.value))
    if(!data.text.trim())throw new Error('未识别到文字，请换一张清晰图片或手动输入。')
    sample.value=''
    text.value=data.text.trim()
    ocrNotice.value='图片识别完成。可修改原文后重新解析。'
  }catch(e){
    parserError.value='图片识别失败：'+(e.message||String(e))
    return
  }finally{
    try{await worker?.terminate()}finally{busy.value=false;ocrProgress.value=''}
  }
  await parse()
}
function showDetail(medicine){
  selected.value=medicine
  detailDialog.value.showModal()
}
function startEdit(medicine){
  selected.value=null
  editing.value={...medicine}
  error.value=''
  message.value=''
  editDialog.value.showModal()
}
async function update(){
  if(busy.value || !editing.value)return
  busy.value=true
  error.value=''
  try{
    const {id,...fields}=editing.value
    await api('/medicines/'+id,{method:'PUT',body:JSON.stringify(fields)})
    editDialog.value.close()
    editing.value=null
    message.value='药品已更新，当前服务将核对状态重置为待核对。'
    await load()
  }catch(e){error.value=e.message}finally{busy.value=false}
}
watch([form,ingredients],()=>{report.value=null;riskAccepted.value=false;confirmed.value=false},{deep:true,flush:'sync'})
async function load(){try{medicines.value=await api('/medicines'+(owner.value?'?owner='+encodeURIComponent(owner.value):''));const member=members.value.find(m=>m.name===owner.value);summary.value=member?await api(`/members/${member.id}/risk-report`):null}catch(e){error.value=e.message}}
const fieldLabels={
  name:'药品名称',spec:'规格',dose:'一次用量',frequency:'频次',method:'服用方式'
}
async function parse(){
  busy.value=true
  parserError.value=''
  message.value=''
  try{
    const card=await post('/instruction/parse',sample.value?{sample_id:sample.value}:{ocr_text:text.value})
    const missing=card.missing_fields || []
    form.value={...empty(),...card,name:missing.includes('name')?'':card.name,owner:form.value.owner||owner.value,expiry_date:''}
    ingredients.value=''
    matches.value=[]
    confirmed.value=false
    const fields=missing.filter(field=>fieldLabels[field]).map(field=>fieldLabels[field])
    message.value=card.demo_only
      ? '已解析演示样例。请对照说明书核对。'
      : fields.length
        ? `已解析。请对照原图补填：${fields.join('、')}。`
        : '已解析。请对照原图核对回填内容。'
    openReview()
    if(form.value.name)await resolveIngredients()
  }catch(e){parserError.value=e.message}finally{busy.value=false}
}
const keyword=ref(''), searching=ref(false), searchStatus=ref('')
let searchRequest=0
function clearSearch(){
  searchRequest++
  searching.value=false
  matches.value=[]
  searchStatus.value=''
}
watch(keyword,clearSearch,{flush:'sync'})
watch(()=>form.value.name,()=>{
  clearSearch()
  ingredientRequest++
  ingredients.value=''
  ingredientStatus.value=''
  resolvingIngredients.value=false
},{flush:'sync'})

async function resolveIngredients(){
  const name=form.value.name.trim()
  if(!name || ingredients.value || resolvingIngredients.value)return
  const request=++ingredientRequest
  resolvingIngredients.value=true
  ingredientStatus.value='正在匹配知识库成分…'
  try{
    const entries=await api('/knowledge/drugs?keyword='+encodeURIComponent(name))
    if(request!==ingredientRequest)return
    const exact=entries.filter(entry=>entry.name===name || entry.aliases?.includes(name))
    if(exact.length===1 && exact[0].ingredients.length){
      ingredients.value=exact[0].ingredients.join('、')
      ingredientStatus.value='来自已发布知识：'+exact[0].name
    }else{
      ingredientStatus.value='未找到唯一的药品成分。请在上方搜索并选择对应药品。'
    }
  }catch(e){
    if(request===ingredientRequest)ingredientStatus.value='成分查询失败，请重试。'+e.message
  }finally{
    if(request===ingredientRequest)resolvingIngredients.value=false
  }
}
async function match(){
  const query=keyword.value.trim()
  if(!query || searching.value)return
  const request=++searchRequest
  searching.value=true
  searchStatus.value=''
  matches.value=[]
  try{
    const results=await api('/knowledge/drugs?keyword='+encodeURIComponent(query))
    if(request!==searchRequest)return
    matches.value=results
    if(!matches.value.length)searchStatus.value='已发布知识中未找到匹配药品。可以识别图片或手动填写。'
  }catch(e){if(request===searchRequest)searchStatus.value=e.message}
  finally{if(request===searchRequest)searching.value=false}
}
function openReview(){
  if(!reviewDialog.value.open)reviewDialog.value.showModal()
}
function closeReview(){
  reviewDialog.value.close()
  report.value=null
  riskAccepted.value=false
  confirmed.value=false
}
function choose(entry){
  if(form.value.name.trim()!==entry.name){
    const hasDraft=Object.entries(form.value).some(([key,value])=>
      key!=='owner' && typeof value==='string' && value.trim()
    )
    if(hasDraft && !window.confirm('选用这条药品会替换当前核对表中的药品信息。继续吗？'))return
    form.value={...empty(),owner:form.value.owner,name:entry.name}
  }
  ingredientRequest++
  resolvingIngredients.value=false
  ingredients.value=entry.ingredients.join('、')
  ingredientStatus.value='来自已发布知识：'+entry.name
  matches.value=[]
  searchStatus.value=''
  message.value='已填入药名和有效成分，请根据手头说明书核对并填写用法。'
  openReview()
}
async function check(){
  if(!confirmed.value || !formValid()){
    error.value='请填写药品信息、匹配有效成分并勾选核对。'
    return false
  }
  busy.value=true
  report.value=null
  riskAccepted.value=false
  try{return await requestRisk()}finally{busy.value=false}
}
async function requestRisk(){const member=members.value.find(m=>m.name===form.value.owner);if(!member){error.value='请选择使用者';return}error.value='';try{report.value=await post('/interactions/check',{member_id:member.id,candidate_name:form.value.name.trim(),candidate_ingredients:ingredientList()});return true}catch(e){error.value=e.message;return false}}
async function save(){
  if(busy.value || !confirmed.value)return
  if(!formValid()){error.value='请匹配有效成分并填写其他必填信息。';return}
  if(!report.value){
    if(await check())message.value='请阅读检查结果，然后确认加入药箱。'
    return
  }
  if(report.value.count && !riskAccepted.value){
    error.value='请阅读风险并确认是否继续加入'
    return
  }
  busy.value=true
  error.value=''
  message.value=''
  try{
    const saved=await post('/medicines',{
      ...form.value,
      name:form.value.name.trim(),
      dose:form.value.dose.trim(),
      frequency:form.value.frequency.trim(),
      confirmed:true,
      ingredients:ingredientList(),
      risk_accepted:riskAccepted.value
    })
    closeReview()
    form.value=empty()
    ingredients.value=''
    message.value=`已将「${saved.name}」加入${saved.owner}的药箱。`
  }catch(e){
    error.value=e.message
    if(e.status===409){report.value=null;riskAccepted.value=false}
  }finally{
    busy.value=false
    await nextTick()
    saveStatus.value?.focus()
  }
}
async function remove(m){if(!confirm(`删除“${m.name}”？关联提醒将停用，历史保留。`))return;try{await api(`/medicines/${m.id}`,{method:'DELETE'});selected.value=null;await load()}catch(e){error.value=e.message}}
onMounted(async()=>{try{members.value=await api('/members')
  if(props.mode==='box')await load()
  else try{samples.value=await api('/instruction/samples')}catch{message.value='演示样例暂不可用，可以手动填写或解析原文。'}}catch(e){error.value=e.message}})
</script>
<template><div ref="saveStatus" tabindex="-1"><p class="error" role="alert" v-if="error">{{error}}</p><p class="feedback" role="status" v-if="message">{{message}}</p></div><template v-if="props.mode==='box'"><section class="hero boxhero"><h2>药箱状态</h2><p>{{owner||'全部成员'}} · {{medicines.length}} 件药品</p><div class="metrics"><div class="metric"><b>{{medicines.length}}</b><span>当前药品</span></div><div class="metric"><b>{{summary?.count??'—'}}</b><span>已收录风险</span></div><div class="metric"><b>{{medicines.filter(m=>!m.confirmed).length}}</b><span>待核对</span></div></div></section><div class="toolbar"><select v-model="owner" @change="load"><option value="">全部成员</option><option v-for="m in members" :key="m.id" :value="m.name">{{m.name}}</option></select><button @click="emit('navigate','风险报告')">用药风险报告</button></div><p class="feedback" v-if="summary">{{summary.highest_level}} · {{summary.message}}</p><article class="medicine-card" v-for="m in medicines" :key="m.id"><div class="boxhead"><div class="boxleft"><div class="boxicon">💊</div><div><h2>{{m.name}}</h2><p>{{[m.owner,m.spec].filter(Boolean).join(' · ')}}</p></div></div><span class="tag" :class="m.confirmed?'green':'orange'">{{m.confirmed?'已核对':'待核对'}}</span></div><div class="meta"><div><small>位置</small><b>{{m.location||'未填写'}}</b></div><div><small>有效期</small><b>{{m.expiry_date||'未填写'}}</b></div><div><small>库存</small><b>{{m.stock||'未填写'}}</b></div></div><div class="scan-actions" v-if="expired(m)||outOfStock(m)">
  <span class="tag red" v-if="expired(m)">已过有效期</span>
  <span class="tag orange" v-if="outOfStock(m)">库存为零</span>
</div><div class="toolbar medicine-card-actions"><button @click="showDetail(m)">药品详情</button><button @click="startEdit(m)">编辑</button><button @click="emit('ask',m.name)">问问 AI</button><button class="quiet" @click="remove(m)">删除</button></div></article><p class="empty" v-if="!medicines.length">药箱暂无药品，核对后添加。</p><dialog ref="editDialog" class="panel editor-dialog" aria-labelledby="medicine-edit-title" @cancel="busy && $event.preventDefault()">
<form v-if="editing" @submit.prevent="update">
  <div class="dialog-heading"><h2 id="medicine-edit-title">编辑 {{editing.name}}</h2><button type="button" class="dialog-close" aria-label="关闭弹窗" :disabled="busy" @click="editDialog.close();editing=null">×</button></div>
  <p v-if="error" class="error" role="alert">{{error}}</p>
  <p class="subtitle">保存后，当前服务会将该药品标为待核对，老人模式暂不可播报。</p>
  <fieldset :disabled="busy">
    <div class="form-grid">
      <label>库存<input v-model="editing.stock"></label>
      <label>存放位置<input v-model="editing.location"></label>
    </div>
    <div class="scan-actions">
      <button type="submit">保存修改</button>

    </div>
  </fieldset>
</form></dialog>
<dialog ref="detailDialog" class="panel editor-dialog" aria-labelledby="medicine-detail-title">
  <div v-if="selected">
    <div class="dialog-heading"><h2 id="medicine-detail-title">{{selected.name}}</h2><button type="button" class="dialog-close" aria-label="关闭弹窗" @click="detailDialog.close()">×</button></div>
    <dl class="medicine-details">
      <dt>使用者</dt><dd>{{selected.owner || '未填写'}}</dd>
      <dt>规格</dt><dd>{{selected.spec || '未填写'}}</dd>
      <dt>有效成分</dt><dd>{{selected.ingredients?.join('、') || '未填写'}}</dd>
      <dt>用法</dt><dd>{{[selected.dose, selected.frequency, selected.method].filter(Boolean).join(' · ') || '未填写'}}</dd>
      <dt>注意事项</dt><dd>{{selected.risks.join('；') || '请核对原说明书'}}</dd>
    </dl>
    <details><summary>保存的原始文字</summary><p>{{selected.original_text || '未保存原文'}}</p></details>
    <div class="scan-actions">
      <button @click="detailDialog.close();emit('ask',selected.name)">就此药询问 AI</button>

    </div>
  </div>
</dialog>
<button class="primary" @click="emit('navigate','扫一扫')">＋ 添加药品</button></template><template v-else>
<section class="panel">
  <div class="drug-search-heading">
    <h2>搜索药品</h2>
    <label for="drug-search">药品名、商品名或有效成分</label>
  </div>
  <form class="search-row" @submit.prevent="match">
    <input id="drug-search" v-model="keyword" type="search" :disabled="searching" required>
    <button :disabled="searching || !keyword.trim()">{{searching?'搜索中…':'搜索'}}</button>
  </form>
  <p v-if="searchStatus" class="subtitle" role="status">{{searchStatus}}</p>
  <ul v-if="matches.length" class="drug-search-results">
    <li v-for="entry in matches" :key="entry.id">
      <div><b>{{entry.name}}</b><div class="subtitle">{{entry.ingredients.join('、')}}</div></div>
      <button type="button" :disabled="busy" @click="choose(entry)">填入核对表</button>
    </li>
  </ul>
</section>
<section class="panel">
<h2>解析药盒或说明书</h2>
<p class="error" v-if="parserError" role="alert">{{parserError}}</p>
<p class="subtitle">选择图片后会自动识别并打开核对弹窗。也可以粘贴原文、加载演示样例或手动核对。</p>
<label>药盒或说明书图片<input type="file" accept="image/*" :disabled="busy" @change="onImageSelected"></label>
<div class="scan-actions"><button :disabled="busy||!image" @click="recognize">重新识别图片</button></div>
<p v-if="ocrProgress || ocrNotice" role="status">{{ocrProgress || ocrNotice}}</p><select v-model="sample" :disabled="busy"><option value="">使用下方原文解析</option><option v-for="s in samples" :key="s.id" :value="s.id">演示样例 · {{s.name}}</option></select><textarea v-model="text" :disabled="busy||!!sample" rows="4" placeholder="粘贴说明书文字"></textarea><button :disabled="busy||(!sample&&!text.trim())" @click="parse">解析并填写核对表</button>
</section>
<button class="secondary" :disabled="busy" @click="openReview">{{form.name?'继续核对药品':'手动核对药品'}}</button>
<button v-if="message.startsWith('已将')" class="secondary medicine-submit" @click="emit('navigate','药箱')">查看药箱</button>
<dialog ref="reviewDialog" class="panel editor-dialog" aria-labelledby="review-title" @cancel.prevent="!busy && closeReview()">
<div class="dialog-heading"><h2 id="review-title">核对药品</h2><button type="button" class="dialog-close" aria-label="关闭弹窗" :disabled="busy" @click="closeReview">×</button></div>
<p v-if="error" class="error" role="alert">{{error}}</p>
<p v-if="message" class="feedback" role="status">{{message}}</p><p v-if="!members.length" class="subtitle">入箱需要家庭成员。<button @click="emit('navigate','家人')">前往家庭成员</button></p><form ref="formElement" @submit.prevent="save"><fieldset :disabled="busy"><div class="form-grid"><label>药品名称 *<input v-model="form.name" @change="resolveIngredients" required></label><label>使用者 *<select v-model="form.owner" required><option value="" disabled>请选择成员</option><option v-for="m in members" :key="m.id" :value="m.name">{{m.name}}</option></select></label></div><label>有效成分<input :value="ingredients" readonly placeholder="从已发布知识自动带入"></label>
<p v-if="ingredientStatus" class="subtitle" role="status">{{ingredientStatus}}</p>
<button v-if="form.name && !ingredients" type="button" :disabled="resolvingIngredients" @click="resolveIngredients">匹配有效成分</button><div class="form-grid"><label>规格<input v-model="form.spec"></label><label>一次用量 *<input v-model="form.dose" required></label><label>频次 *<input v-model="form.frequency" required></label><label>服用方式<input v-model="form.method"></label><label>库存<input v-model="form.stock"></label><label>存放位置<input v-model="form.location"></label><label>有效期<input type="date" v-model="form.expiry_date"></label></div><label class="check"><input type="checkbox" v-model="confirmed">我已核对药名、有效成分、使用者和用法用量</label><div v-if="report"><p class="feedback">{{report.message}}</p><p class="error" v-if="report.missing.length">资料不足：{{report.missing.join('、')}}，未命中不代表安全。</p><details v-for="risk in report.items" :key="risk.id"><summary>{{risk.level}} · {{risk.drugs.join(' ＋ ')}}</summary><KnowledgeDetail :entry="risk"/></details><label class="check" v-if="report.count"><input type="checkbox" v-model="riskAccepted">我已阅读风险和依据，知晓需咨询医生或药师，仍选择加入</label><button type="button" v-if="report.count" @click="emit('navigate','药箱')">暂不加入，返回药箱</button></div><button class="primary medicine-submit" :disabled="busy||!confirmed||!ingredients.trim()||(report?.count>0 && !riskAccepted)">{{busy?'处理中…':report?'确认加入药箱':'检查用药风险'}}</button></fieldset></form></dialog></template></template>
