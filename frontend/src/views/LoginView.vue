<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'
import { useAuthStore } from '../stores/auth'

const username = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)
const auth = useAuthStore()
const router = useRouter()

async function login() {
  error.value = ''
  loading.value = true
  try {
    const response = await api.post<{ access_token: string }>('/auth/login', {
      username: username.value,
      password: password.value,
    })
    auth.setToken(response.data.access_token)
    router.push('/meetings')
  } catch {
    error.value = '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="login-page">
    <form class="panel login-form" @submit.prevent="login">
      <div>
        <h1>会议纪要智能整理</h1>
        <p class="muted">登录后处理会议转写、纪要和待办。</p>
      </div>
      <label class="field">
        <span>用户名</span>
        <input v-model="username" class="input" autocomplete="username" required />
      </label>
      <label class="field">
        <span>密码</span>
        <input v-model="password" class="input" type="password" autocomplete="current-password" required />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="button" type="submit" :disabled="loading">{{ loading ? '登录中' : '登录' }}</button>
    </form>
  </main>
</template>
