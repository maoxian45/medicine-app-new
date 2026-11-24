<script setup>
import {ref,onMounted} from 'vue'
import {api,post} from '../api'
const members=ref([]),error=ref(''),busy=ref(false),editing=ref(null)
const fresh=()=>({name:'',age:'',weight:'',allergy:'',role:'成人',emoji:'🙂'})
const form=ref(fresh())
const editor=ref(null)
async function load(){try{members.value=await api('/members')}catch(e){error.value=e.message}}
function edit(m){
  editing.value=m?.id ?? null
  form.value=m ? {...m} : fresh()
  error.value=''
  editor.value.showModal()
}
async function save(){busy.value=true;error.value='';try{await api('/members'+(editing.value?'/'+editing.value:''),{method:editing.value?'PUT':'POST',body:JSON.stringify({...form.value,name:form.value.name.trim()})});editor.value.close();await load()}catch(e){error.value=e.message}finally{busy.value=false}}
async function remove(m){if(!confirm(`删除成员“${m.name}”？历史记录保留。`))return;try{await api('/members/'+m.id,{method:'DELETE'});await load()}catch(e){error.value=e.message}}
onMounted(load)
</script>
<template><div class="toolbar"><button @click="edit()">＋ 添加成员</button></div><p class="error" v-if="error && !editor?.open">{{error}}</p><div class="cards member-list"><article v-for="m in members" :key="m.id"><div class="member-head"><div class="avatar">{{m.emoji}}</div><div><h2>{{m.name}}</h2><p>{{m.role}}{{m.age && m.age!==m.role ? ' · '+m.age : ''}}</p></div></div><p>体重：{{m.weight||'未填写'}} · 过敏史：{{m.allergy||'未填写'}}</p><div class="member-actions"><button @click="edit(m)">编辑</button><button class="quiet" @click="remove(m)">删除成员</button></div></article></div><dialog ref="editor" class="panel editor-dialog" aria-labelledby="member-editor-title" @cancel="busy && $event.preventDefault()"><div class="dialog-heading"><h2 id="member-editor-title">{{editing?'编辑成员':'添加家庭成员'}}</h2><button type="button" class="dialog-close" aria-label="关闭弹窗" :disabled="busy" @click="editor.close()">×</button></div><form @submit.prevent="save"><p class="error" v-if="error" role="alert">{{error}}</p><div class="form-grid"><label>姓名 *<input v-model="form.name" required maxlength="40"></label><label>年龄<input v-model="form.age" placeholder="如 76 岁"></label><label>体重<input v-model="form.weight" placeholder="如 68 kg"></label><label>角色<select v-model="form.role"><option>成人</option><option>老人</option><option>儿童</option><option>照护者</option></select></label><label>过敏史<input v-model="form.allergy"></label></div><button class="primary" :disabled="busy||!form.name.trim()">{{busy?'保存中…':'保存成员'}}</button></form></dialog></template>
