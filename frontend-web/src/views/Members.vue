<script setup>
import {ref,onMounted} from 'vue'
import {api,post} from '../api'
const members=ref([]),error=ref(''),busy=ref(false),editing=ref(null)
const fresh=()=>({name:'',age:'',weight:'',allergy:'',role:'成人',emoji:'🙂'})
const form=ref(fresh())
async function load(){try{members.value=await api('/members')}catch(e){error.value=e.message}}
function edit(m){editing.value=m.id;form.value={...m}}
async function save(){busy.value=true;error.value='';try{await api('/members'+(editing.value?'/'+editing.value:''),{method:editing.value?'PUT':'POST',body:JSON.stringify({...form.value,name:form.value.name.trim()})});form.value=fresh();editing.value=null;await load()}catch(e){error.value=e.message}finally{busy.value=false}}
async function remove(m){if(!confirm(`删除成员“${m.name}”？历史记录保留。`))return;try{await api('/members/'+m.id,{method:'DELETE'});await load()}catch(e){error.value=e.message}}
onMounted(load)
</script>
<template><section class="hero"><h2>家庭成员</h2><p>为家人管理独立药箱，关心每一次用药。</p></section><p class="error" v-if="error">{{error}}</p><div class="cards"><article v-for="m in members" :key="m.id"><div class="member-head"><div class="avatar">{{m.emoji}}</div><div><h2>{{m.name}}</h2><p>{{m.role}} · {{m.age||'年龄未填写'}}</p></div></div><p>体重：{{m.weight||'未填写'}} · 过敏史：{{m.allergy||'未填写'}}</p><button @click="edit(m)">编辑</button><button class="quiet" @click="remove(m)">删除成员</button></article></div><section class="panel"><h2>{{editing?'编辑成员':'添加家庭成员'}}</h2><form @submit.prevent="save"><div class="form-grid"><label>姓名 *<input v-model="form.name" required maxlength="40"></label><label>年龄<input v-model="form.age" placeholder="如 76 岁"></label><label>体重<input v-model="form.weight" placeholder="如 68 kg"></label><label>角色<select v-model="form.role"><option>成人</option><option>老人</option><option>儿童</option><option>照护者</option></select></label><label>过敏史<input v-model="form.allergy"></label></div><button class="primary" :disabled="busy||!form.name.trim()">{{busy?'保存中…':'保存成员'}}</button><button type="button" v-if="editing" @click="editing=null;form=fresh()">取消编辑</button></form></section></template>
