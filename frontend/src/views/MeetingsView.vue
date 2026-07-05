<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api/client'
import type { Meeting } from '../api/types'

const meetings = ref<Meeting[]>([])
const loading = ref(false)
const error = ref('')

const statusLabels: Record<string, string> = {
  draft: '草稿',
  processing: '处理中',
  ready: '已就绪',
  failed: '失败',
}

const sourceLabels: Record<string, string> = {
  audio: '音频',
  manual_text: '文本',
}

function formatTime(value: string) {
  return new Date(value).toLocaleString()
}

async function loadMeetings() {
  loading.value = true
  error.value = ''
  try {
    const response = await api.get<Meeting[]>('/meetings')
    meetings.value = response.data
  } catch {
    error.value = '加载会议列表失败'
  } finally {
    loading.value = false
  }
}

onMounted(loadMeetings)
</script>

<template>
  <main class="page">
    <div class="toolbar">
      <div>
        <h1>会议</h1>
        <p class="muted">查看历史会议和处理状态。</p>
      </div>
      <RouterLink class="button" to="/meetings/new">新建会议</RouterLink>
    </div>

    <section class="panel">
      <p v-if="loading" class="muted">加载中</p>
      <p v-else-if="error" class="error">{{ error }}</p>
      <table v-else class="table">
        <thead>
          <tr>
            <th>标题</th>
            <th>状态</th>
            <th>来源</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="meeting in meetings" :key="meeting.id">
            <td>{{ meeting.title }}</td>
            <td>{{ statusLabels[meeting.status] ?? meeting.status }}</td>
            <td>{{ sourceLabels[meeting.source_type] ?? meeting.source_type }}</td>
            <td>{{ formatTime(meeting.meeting_time) }}</td>
            <td><RouterLink class="text-link" :to="`/meetings/${meeting.id}`">查看</RouterLink></td>
          </tr>
          <tr v-if="meetings.length === 0">
            <td class="muted" colspan="5">暂无会议</td>
          </tr>
        </tbody>
      </table>
    </section>
  </main>
</template>
