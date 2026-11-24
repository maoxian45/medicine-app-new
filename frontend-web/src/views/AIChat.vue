<script setup>
import {ref,onMounted} from 'vue'
import {api,post} from '../api'
const props=defineProps({drugName:{type:String,default:''}})
const question=ref(props.drugName?`请介绍${props.drugName}的注意事项`:''),sessions=ref([]),sessionId=ref(null),messages=ref([]),error=ref(''),busy=ref(false),configured=ref(false)
async function refresh(){sessions.value=await api('/ai/sessions')}
async function select(){error.value='';try{messages.value=sessionId.value?await api('/ai/sessions/'+sessionId.value):[]}catch(e){error.value=e.message}}
async function send(){busy.value=true;error.value='';try{const result=await post('/ai/chat',{question:question.value,session_id:sessionId.value,drug_name:props.drugName});sessionId.value=result.session_id;question.value='';await select();await refresh()}catch(e){error.value=e.message}finally{busy.value=false}}
onMounted(async()=>{try{configured.value=(await api('/ai/status')).configured;await refresh()}catch(e){error.value=e.message}})
</script>
<template><div class="feedback ai-disclaimer">AI 用药知识助手 · 不替代医生或药师，不提供诊断、处方或调药建议。</div><p class="error" v-if="!configured">模型服务尚未配置。可查看入口和历史；真实问答需管理员在管理端填写配置。</p><label>会话历史<select v-model="sessionId" @change="select"><option :value="null">＋ 新会话</option><option v-for="s in sessions" :key="s.id" :value="s.id">{{s.title}}</option></select></label><p class="subtitle" v-if="props.drugName">当前药品：{{props.drugName}}</p><div class="chat-message" :class="m.role" v-for="m in messages" :key="m.id"><b>{{m.role==='user'?'我的问题':'知识助手'}}</b><p>{{m.content}}</p><details v-if="m.sources.length"><summary>参考资料 {{m.sources.length}} 条</summary><p v-for="s in m.sources" :key="s.id"><a :href="s.source_url" target="_blank" rel="noopener noreferrer">{{s.source_name}}</a><br>{{s.chapter}} · {{s.source_version}}</p></details></div><p class="error" role="alert" v-if="error">{{error}}</p><form class="panel" @submit.prevent="send"><label>用药知识问题<textarea v-model="question" maxlength="2000" rows="4" placeholder="例如：布洛芬有哪些注意事项？"></textarea></label><p class="subtitle">只发送问题和所需知识资料；请勿输入姓名等身份信息。</p><button class="primary" :disabled="busy || !question.trim()">{{busy?'正在处理…':'发送问题'}}</button></form></template>

<style scoped>
.ai-disclaimer { font-size: 14px; }
</style>
