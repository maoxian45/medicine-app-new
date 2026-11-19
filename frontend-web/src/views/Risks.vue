<script setup>
import {ref,onMounted} from 'vue'
import {api} from '../api'
import KnowledgeDetail from '../components/KnowledgeDetail.vue'
const members=ref([]),memberId=ref(''),report=ref(null),error=ref(''),busy=ref(false)
async function load(){report.value=null;if(!memberId.value)return;busy.value=true;error.value='';try{report.value=await api(`/members/${memberId.value}/risk-report`)}catch(e){error.value=e.message}finally{busy.value=false}}
onMounted(async()=>{try{members.value=await api('/members');memberId.value=members.value[0]?.id||'';await load()}catch(e){error.value=e.message}})
</script>
<template><label>查看成员<select v-model="memberId" @change="load"><option v-for="m in members" :key="m.id" :value="m.id">{{m.name}}</option></select></label><button @click="load" :disabled="busy">重新扫描风险</button><p class="error" v-if="error">{{error}}</p><template v-if="report"><section class="hero"><h2>{{report.member_name}}的用药风险</h2><p>{{report.count}} 项 · {{report.highest_level}}</p></section><p class="feedback">{{report.message}}</p><p class="error" v-if="report.missing.length">以下药品资料不足：{{report.missing.join('、')}}。不能据此判断安全。</p><section class="panel" v-for="item in report.items" :key="item.id"><p>{{item.drugs.join(' ＋ ')}}</p><KnowledgeDetail :entry="item"/></section><section class="panel" v-if="report.population_notes.length"><h2>特殊人群提示</h2><p class="subtitle">请结合成员年龄及过敏史核对；当前为资料提示，不作个体诊断。</p><p v-for="n in report.population_notes" :key="n.drug">{{n.drug}}：{{n.text}}</p></section></template></template>
