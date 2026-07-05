<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <strong>Meeting AI</strong>
        <span>会议纪要</span>
      </div>
      <nav class="nav">
        <router-link to="/meetings">会议</router-link>
        <router-link to="/tasks">待办</router-link>
      </nav>
      <button class="button ghost sidebar-logout" type="button" @click="logout">退出</button>
    </aside>
    <section class="content">
      <router-view />
    </section>
  </div>
</template>
