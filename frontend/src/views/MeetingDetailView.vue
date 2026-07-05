<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { api } from '../api/client'
import type { AiJob, AsrJob, Meeting, MeetingSummary, TodoDraft, Transcript } from '../api/types'
import TodoDraftEditor from '../components/TodoDraftEditor.vue'
import { shouldPollMeetingDetail } from '../utils/polling'

const route = useRoute()
const meetingId = computed(() => Number(route.params.id))
const meeting = ref<Meeting | null>(null)
const transcripts = ref<Transcript[]>([])
const summary = ref<MeetingSummary | null>(null)
const todoDrafts = ref<TodoDraft[]>([])
const aiJobs = ref<AiJob[]>([])
const asrJobs = ref<AsrJob[]>([])
const loading = ref(false)
const error = ref('')
const pollTimer = ref<number | null>(null)

const latestTranscript = computed(() => transcripts.value[0])
const latestAiJob = computed(() => aiJobs.value[0])
const latestAsrJob = computed(() => asrJobs.value[0])

const statusLabels: Record<string, string> = {
  draft: '草稿',
  processing: '处理中',
  ready: '已就绪',
  failed: '失败',
  pending: '等待中',
  succeeded: '已成功',
}

function listItems(value: { items: string[] } | undefined) {
  return value?.items ?? []
}

async function loadDetail() {
  loading.value = true
  error.value = ''
  try {
    const [meetingResponse, transcriptResponse, aiJobResponse, asrJobResponse, draftResponse] = await Promise.all([
      api.get<Meeting>(`/meetings/${meetingId.value}`),
      api.get<Transcript[]>(`/meetings/${meetingId.value}/transcripts`),
      api.get<AiJob[]>(`/meetings/${meetingId.value}/ai-jobs`),
      api.get<AsrJob[]>(`/meetings/${meetingId.value}/asr-jobs`),
      api.get<TodoDraft[]>(`/meetings/${meetingId.value}/todo-drafts`),
    ])
    meeting.value = meetingResponse.data
    transcripts.value = transcriptResponse.data
    aiJobs.value = aiJobResponse.data
    asrJobs.value = asrJobResponse.data
    todoDrafts.value = draftResponse.data

    try {
      const summaryResponse = await api.get<MeetingSummary>(`/meetings/${meetingId.value}/summary`)
      summary.value = summaryResponse.data
    } catch {
      summary.value = null
    }
  } catch {
    error.value = '加载会议详情失败'
  } finally {
    loading.value = false
  }
}

function stopPolling() {
  if (pollTimer.value !== null) {
    window.clearInterval(pollTimer.value)
    pollTimer.value = null
  }
}

function syncPolling() {
  if (shouldPollMeetingDetail(meeting.value, aiJobs.value, asrJobs.value)) {
    if (pollTimer.value === null) {
      pollTimer.value = window.setInterval(loadDetail, 3000)
    }
  } else {
    stopPolling()
  }
}

async function refreshDetail() {
  await loadDetail()
  syncPolling()
}

onMounted(refreshDetail)
onBeforeUnmount(stopPolling)
</script>

<template>
  <main class="page">
    <div class="toolbar">
      <div>
        <h1>{{ meeting?.title ?? '会议详情' }}</h1>
        <p class="muted">转写、纪要和待办草稿。</p>
      </div>
      <button class="button secondary" type="button" @click="refreshDetail">刷新</button>
    </div>

    <p v-if="loading" class="muted">加载中</p>
    <p v-else-if="error" class="error">{{ error }}</p>

    <div v-else class="grid">
      <section class="panel detail-grid">
        <div>
          <span class="meta-label">会议状态</span>
          <strong>{{ statusLabels[meeting?.status ?? ''] ?? meeting?.status }}</strong>
        </div>
        <div>
          <span class="meta-label">ASR 状态</span>
          <strong>{{ statusLabels[latestAsrJob?.status ?? ''] ?? latestAsrJob?.status ?? '-' }}</strong>
        </div>
        <div>
          <span class="meta-label">AI 状态</span>
          <strong>{{ statusLabels[latestAiJob?.status ?? ''] ?? latestAiJob?.status ?? '-' }}</strong>
        </div>
      </section>

      <section class="panel">
        <h2>转写文本</h2>
        <pre class="transcript">{{ latestTranscript?.content ?? '暂无转写文本' }}</pre>
      </section>

      <section class="panel">
        <h2>结构化纪要</h2>
        <div v-if="summary" class="summary-grid">
          <div>
            <span class="meta-label">会议主题</span>
            <strong>{{ summary.topic }}</strong>
          </div>
          <div>
            <span class="meta-label">参与人员</span>
            <p>{{ listItems(summary.participants_json).join('、') || '-' }}</p>
          </div>
          <div>
            <span class="meta-label">讨论要点</span>
            <ul>
              <li v-for="item in listItems(summary.key_points_json)" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div>
            <span class="meta-label">决议事项</span>
            <ul>
              <li v-for="item in listItems(summary.decisions_json)" :key="item">{{ item }}</li>
            </ul>
          </div>
        </div>
        <p v-else class="muted">暂无纪要结果</p>
      </section>

      <section class="panel">
        <div class="toolbar compact-toolbar">
          <h2>待办草稿</h2>
          <span class="muted">{{ todoDrafts.length }} 条</span>
        </div>
        <div class="draft-list">
          <TodoDraftEditor
            v-for="draft in todoDrafts"
            :key="draft.id"
            :draft="draft"
            @confirmed="refreshDetail"
            @discarded="refreshDetail"
          />
          <p v-if="todoDrafts.length === 0" class="muted">暂无待办草稿</p>
        </div>
      </section>
    </div>
  </main>
</template>
