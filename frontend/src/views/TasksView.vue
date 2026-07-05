<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../api/client'
import type { Meeting, Task, TaskStatus, User } from '../api/types'
import StatusBadge from '../components/StatusBadge.vue'
import TaskStatusTabs from '../components/TaskStatusTabs.vue'

const status = ref<TaskStatus | ''>('')
const tasks = ref<Task[]>([])
const meetings = ref<Meeting[]>([])
const users = ref<User[]>([])
const loading = ref(false)
const error = ref('')

const meetingById = computed(() => new Map(meetings.value.map((meeting) => [meeting.id, meeting])))
const userById = computed(() => new Map(users.value.map((user) => [user.id, user])))

function formatDate(value: string | null) {
  if (!value) {
    return '-'
  }
  return new Date(value).toLocaleDateString()
}

function meetingTitle(meetingId: number) {
  return meetingById.value.get(meetingId)?.title ?? `会议 #${meetingId}`
}

function assigneeName(userId: number) {
  const user = userById.value.get(userId)
  return user ? `${user.display_name}（${user.username}）` : `#${userId}`
}

async function loadTasks() {
  loading.value = true
  error.value = ''
  try {
    const params = status.value ? { status: status.value } : undefined
    const response = await api.get<Task[]>('/tasks', { params })
    tasks.value = response.data
  } catch {
    error.value = '加载待办失败'
  } finally {
    loading.value = false
  }
}

async function loadMeetings() {
  try {
    const response = await api.get<Meeting[]>('/meetings')
    meetings.value = response.data
  } catch {
    meetings.value = []
  }
}

async function loadUsers() {
  try {
    const response = await api.get<User[]>('/users/assignees')
    users.value = response.data
  } catch {
    users.value = []
  }
}

async function updateStatus(task: Task, nextStatus: TaskStatus) {
  error.value = ''
  try {
    await api.patch(`/tasks/${task.id}/status`, { status: nextStatus })
    await loadTasks()
  } catch {
    error.value = '更新待办状态失败'
  }
}

onMounted(async () => {
  await Promise.all([loadMeetings(), loadUsers(), loadTasks()])
})

watch(status, loadTasks)
</script>

<template>
  <main class="page">
    <div class="toolbar">
      <div>
        <h1>待办追踪</h1>
        <p class="muted">按状态筛选并更新会议产生的待办。</p>
      </div>
      <TaskStatusTabs v-model="status" />
    </div>

    <section class="panel">
      <p v-if="loading" class="muted">加载中</p>
      <p v-else-if="error" class="error">{{ error }}</p>
      <table v-else class="table">
        <thead>
          <tr>
            <th>任务</th>
            <th>会议</th>
            <th>负责人</th>
            <th>截止日期</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="task in tasks" :key="task.id">
            <td>
              <strong>{{ task.title }}</strong>
              <p class="muted table-note">{{ task.description }}</p>
            </td>
            <td>{{ meetingTitle(task.meeting_id) }}</td>
            <td>{{ assigneeName(task.assignee_id) }}</td>
            <td>{{ formatDate(task.due_date) }}</td>
            <td><StatusBadge :status="task.status" /></td>
            <td>
              <div class="toolbar-actions">
                <button class="button secondary" type="button" :disabled="task.status === 'todo'" @click="updateStatus(task, 'todo')">
                  待开始
                </button>
                <button class="button secondary" type="button" :disabled="task.status === 'doing'" @click="updateStatus(task, 'doing')">
                  进行中
                </button>
                <button class="button secondary" type="button" :disabled="task.status === 'done'" @click="updateStatus(task, 'done')">
                  已完成
                </button>
              </div>
            </td>
          </tr>
          <tr v-if="tasks.length === 0">
            <td class="muted" colspan="6">暂无待办</td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>
