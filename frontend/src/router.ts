import { createRouter, createWebHistory } from 'vue-router'
import LoginView from './views/LoginView.vue'
import MeetingDetailView from './views/MeetingDetailView.vue'
import MeetingsView from './views/MeetingsView.vue'
import NewMeetingView from './views/NewMeetingView.vue'
import TasksView from './views/TasksView.vue'
import { useAuthStore } from './stores/auth'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView },
    { path: '/', redirect: '/meetings' },
    { path: '/meetings', component: MeetingsView, meta: { requiresAuth: true } },
    { path: '/meetings/new', component: NewMeetingView, meta: { requiresAuth: true } },
    { path: '/meetings/:id', component: MeetingDetailView, meta: { requiresAuth: true } },
    { path: '/tasks', component: TasksView, meta: { requiresAuth: true } },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return '/login'
  }
  return true
})
