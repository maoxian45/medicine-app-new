<script setup>
import { computed,ref,onMounted,onBeforeUnmount } from 'vue'
import Members from './views/Members.vue'
import Medicines from './views/Medicines.vue'
import Records from './views/Records.vue'
import Home from './views/Home.vue'
import Knowledge from './views/Knowledge.vue'
import AIChat from './views/AIChat.vue'
import Risks from './views/Risks.vue'
import Elder from './views/Elder.vue'
import Admin from './views/Admin.vue'
import Login from './views/Login.vue'
import { api } from './api'
const isAdmin=location.pathname.startsWith('/admin')
const logged=ref(!!sessionStorage.getItem(isAdmin?'admin_token':'family_token'))
const page=ref('首页'),elder=ref(localStorage.getItem('elder_mode')==='true'),drugName=ref('')
const previousPages=ref([])
const backPage=computed(()=>previousPages.value.at(-1))
const tabs=[['🏠','首页'],['📷','扫一扫'],['🧰','药箱'],['👨‍👩‍👧','家人'],['⚙️','我的']]
const activeTab=computed(()=>({
  '风险报告':'药箱',
  '提醒记录':'我的',
  '用药知识':'我的',
  'AI助手':'我的'
})[page.value] || page.value)
const title=computed(()=>elder.value&&logged.value?'👴 老人模式':({'首页':'药明白','扫一扫':'添加药品','药箱':'家庭药箱','家人':'家庭成员','我的':'我的','提醒记录':'提醒与记录','用药知识':'用药知识','AI助手':'AI 用药知识助手','风险报告':'用药风险报告'})[page.value])
const subtitle=computed(()=>({'首页':'你好，欢迎回家','扫一扫':'识别 · 核对 · 风险检查','药箱':'按成员管理与风险查看','家人':'一起守护家人健康','我的':'个人与家庭设置','提醒记录':'按时服药，安心记录','用药知识':'查询已审核知识与来源','AI助手':'资料辅助 · 支持多轮追问','风险报告':'可追溯资料与确定性规则'})[page.value])
function showPage(value){
  page.value=value
  window.scrollTo(0,0)
}
function go(value){
  if(value===page.value)return
  const existing=previousPages.value.lastIndexOf(value)
  if(existing>=0)previousPages.value.splice(existing)
  else previousPages.value.push(page.value)
  showPage(value)
}
function openTab(value){
  previousPages.value=[]
  showPage(value)
}
function goBack(){
  if(backPage.value)showPage(previousPages.value.pop())
}
function navigate(value){if(value==='AI助手')drugName.value='';go(value)}
function ask(name){drugName.value=name;go('AI助手')}
function exitElder(){mode(false);openTab('我的')}
function mode(value){elder.value=value;localStorage.setItem('elder_mode',String(value));window.speechSynthesis?.cancel()}
async function logout(){const key=isAdmin?'admin_token':'family_token';try{await api('/auth/logout',{method:'POST',headers:{Authorization:'Bearer '+sessionStorage.getItem(key)}})}finally{sessionStorage.removeItem(key);logged.value=false}}
function expired(event){if(event.detail===(isAdmin?'admin_token':'family_token'))logged.value=false}
onMounted(()=>window.addEventListener('auth-expired',expired))
onBeforeUnmount(()=>window.removeEventListener('auth-expired',expired))
</script>
<template><template v-if="isAdmin"><div class="admin-login" v-if="!logged"><Login admin @logged="logged=true"/></div><Admin v-else @logout="logout"/></template><div v-else class="family-app" :class="{elder:elder&&logged}"><header class="header">
<button v-if="logged && !elder && backPage" type="button" class="page-back" @click="goBack"><span aria-hidden="true">‹</span> 返回{{backPage}}</button>
<div class="headrow"><div class="title"><small>{{elder?'大字号 · 清晰操作':subtitle}}</small><h1>{{title}}</h1></div><button class="iconbtn" v-if="logged&&!elder" aria-label="我的" title="我的" @click="go('我的')"><span aria-hidden="true">👩</span></button><button v-else-if="logged && elder" class="elder-exit" @click="exitElder">退出简易模式</button></div></header><main class="content"><Login v-if="!logged" @logged="logged=true"/><Elder v-else-if="elder" @exit="exitElder"/><template v-else><Home v-if="page==='首页'" @navigate="navigate"/><Medicines v-else-if="page==='扫一扫'||page==='药箱'" :key="page" :mode="page==='扫一扫'?'scan':'box'" @navigate="go" @ask="ask"/><Members v-else-if="page==='家人'"/><Records v-else-if="page==='提醒记录'"/><Knowledge v-else-if="page==='用药知识'" @ask="ask"/><AIChat v-else-if="page==='AI助手'" :key="drugName" :drug-name="drugName"/><Risks v-else-if="page==='风险报告'"/><template v-else><section class="card"><div class="member-head"><div class="avatar">👩</div><div><h3 style="margin:0">我的家庭</h3><p class="subtitle">药明白 · 家庭用药助手</p></div></div></section><div class="section"><h3>知识与安全</h3></div><div class="menu"><button @click="go('用药知识')">📖　用药知识与来源　›</button><button @click="drugName='';go('AI助手')">💬　AI 用药知识助手　›</button></div><div class="section"><h3>家庭与服药</h3></div><div class="menu"><button @click="go('家人')">👨‍👩‍👧　家庭成员管理　›</button><button @click="go('药箱')">🧰　家庭药箱　›</button><button @click="go('提醒记录')">📋　提醒与服药记录　›</button><button @click="mode(true)">👴　进入老人简易模式　›</button><button @click="logout">退出家庭登录</button></div><div class="section"><h3>使用说明</h3></div><section class="card"><p class="subtitle">识别结果须核对后保存；服药记录可撤销误确认。网页关闭或通知不可用时不保证弹出提醒。用药以原说明书及医生、药师指导为准。</p><a href="/admin" target="_blank">打开独立知识库管理端 ↗</a></section></template></template></main><nav class="nav" v-if="logged&&!elder"><button v-for="[icon,name] in tabs" :key="name" :class="{active:activeTab===name}" :aria-current="page===name ? 'page' : undefined" @click="openTab(name)"><span>{{icon}}</span>{{name}}</button></nav></div></template>
