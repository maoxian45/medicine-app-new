<script setup>
import {ref,onMounted} from 'vue'
import {api} from '../api'
import KnowledgeDetail from '../components/KnowledgeDetail.vue'
const members=ref([]),memberId=ref(''),report=ref(null),error=ref(''),busy=ref(false)
async function load(){report.value=null;if(!memberId.value)return;busy.value=true;error.value='';try{report.value=await api(`/members/${memberId.value}/risk-report`)}catch(e){error.value=e.message}finally{busy.value=false}}
onMounted(async()=>{try{members.value=await api('/members');memberId.value=members.value[0]?.id||'';await load()}catch(e){error.value=e.message}})
</script>
<template><p class="subtitle">按成员检查药箱里的在用药品，查看哪些药品组合命中已发布的相互作用规则，以及提示依据。</p><div class="toolbar risk-controls"><label>查看成员<select v-model="memberId" @change="load" :disabled="busy"><option v-for="m in members" :key="m.id" :value="m.id">{{m.name}}</option></select></label><button @click="load" :disabled="busy || !memberId">{{busy?'检查中…':'重新检查'}}</button></div><p class="error" v-if="error">{{error}}</p><template v-if="report"><section class="hero"><h2>{{report.member_name}}的用药风险</h2><p>{{report.count}} 项 · {{report.highest_level}}</p></section><p class="feedback" v-if="report.count">{{report.message}}</p><p class="subtitle" v-else>当前没有命中已发布的组合风险规则。药箱为空时也会显示 0 项。</p><p class="error" v-if="report.missing.length">以下药品资料不足：{{report.missing.join('、')}}。不能据此判断安全。</p><section class="panel" v-for="item in report.items" :key="item.id"><p>{{item.drugs.join(' ＋ ')}}</p><KnowledgeDetail :entry="item"/></section><section class="panel" v-if="report.population_notes.length"><h2>特殊人群提示</h2><p class="subtitle">请结合成员年龄及过敏史核对；当前为资料提示，不作个体诊断。</p><p v-for="n in report.population_notes" :key="n.drug">{{n.drug}}：{{n.text}}</p></section></template></template>
