<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import AppShell from './components/AppShell.vue'
import { useAuthStore } from './stores/auth'

const auth = useAuthStore()
const route = useRoute()
const useStandaloneRoute = computed(() => route.path === '/login' || !auth.isAuthenticated)
</script>

<template>
  <router-view v-if="useStandaloneRoute" />
  <AppShell v-else />
</template>
