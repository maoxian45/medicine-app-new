<script setup>
import { ref } from 'vue'
import { post } from '../api'
const props=defineProps({admin:Boolean})
const emit=defineEmits(['logged'])
const username=ref(props.admin?'admin':'family'),password=ref(''),error=ref(''),busy=ref(false)
async function login(){busy.value=true;error.value='';try{const result=await post('/auth/login',{username:username.value,password:password.value});if(result.role!==(props.admin?'admin':'family'))throw new Error('请使用对应身份登录入口');sessionStorage.setItem(props.admin?'admin_token':'family_token',result.token);emit('logged')}catch(e){error.value=e.message}finally{busy.value=false}}
</script>
<template><section class="panel login-panel"><h2>{{admin?'知识库管理员登录':'欢迎使用药明白'}}</h2><p class="subtitle">{{admin?'独立管理知识、规则、来源与版本，不访问家庭隐私数据。':'家庭用户入口 · 药箱、提醒、知识与 AI'}}</p><form @submit.prevent="login"><label>账号<input v-model="username" autocomplete="username" required></label><label>密码<input type="password" v-model="password" autocomplete="current-password" required></label><p class="error" v-if="error">{{error}}</p><button class="primary" :disabled="busy">{{busy?'登录中…':'登录'}}</button></form><p class="subtitle">本地演示账号：{{admin?'admin / admin-demo':'family / family-demo'}}</p><a :href="admin?'/':'/admin'">{{admin?'进入家庭用户端':'知识库管理端 →'}}</a></section></template>
