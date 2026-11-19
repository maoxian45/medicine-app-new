<script setup>
import {ref,onMounted} from 'vue'
import {api,post} from '../api'
import KnowledgeDetail from '../components/KnowledgeDetail.vue'
const emit=defineEmits(['ask'])
const keyword=ref(''),items=ref([]),selected=ref(null),error=ref(''),feedback=ref(''),notice=ref(''),busy=ref(false)
async function search(){busy.value=true;error.value='';try{items.value=await api('/knowledge/drugs?keyword='+encodeURIComponent(keyword.value));selected.value=null}catch(e){error.value=e.message}finally{busy.value=false}}
async function send(){try{notice.value=(await post('/knowledge/feedback',{entry_id:selected.value.id,message:feedback.value})).message;feedback.value=''}catch(e){error.value=e.message}}
onMounted(search)
</script>
<template><form class="search-row" @submit.prevent="search"><input v-model="keyword" placeholder="搜索药名、商品名或成分" aria-label="检索药品知识"><button :disabled="busy">搜索</button></form><p class="error" v-if="error">{{error}}</p><p class="subtitle">仅展示已审核且启用的资料。未收录不代表安全。</p><p class="empty" v-if="!busy && !items.length">暂未收录匹配资料。管理员可在独立管理端添加并审核。</p><article v-for="item in items" :key="item.id"><h2>{{item.name}}</h2><p>{{item.ingredients.join('、')}}</p><button @click="selected=item;notice=''">查看知识与来源</button><button @click="emit('ask',item.name)">问问 AI</button></article><section class="panel" v-if="selected"><KnowledgeDetail :entry="selected"/><button @click="emit('ask',selected.name)">就此药品询问 AI</button><hr><label>知识纠错反馈<textarea v-model="feedback" maxlength="2000" placeholder="说明哪项内容需要核实"></textarea></label><button :disabled="!feedback.trim()" @click="send">提交反馈</button><p class="feedback" v-if="notice">{{notice}}</p></section></template>
