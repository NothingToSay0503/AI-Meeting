<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { api } from '../api/client'
import type { DraftStatus, TodoDraft, User } from '../api/types'

const props = defineProps<{ draft: TodoDraft }>()
const emit = defineEmits<{ confirmed: []; discarded: [] }>()

const assigneeId = ref(props.draft.assignee_id ? String(props.draft.assignee_id) : '')
const dueDate = ref(props.draft.due_date ?? '')
const title = ref(props.draft.description.slice(0, 80))
const description = ref(props.draft.description)
const error = ref('')
const loading = ref(false)
const users = ref<User[]>([])

const draftStatusLabels: Record<DraftStatus, string> = {
  draft: '待确认',
  confirmed: '已确认',
  discarded: '已丢弃',
}

const draftStatusLabel = computed(() => draftStatusLabels[props.draft.status])

function userLabel(user: User) {
  return `${user.display_name}（${user.username}）`
}

function applyDraftAssignee(draft: TodoDraft) {
  if (draft.assignee_id) {
    assigneeId.value = String(draft.assignee_id)
    return
  }
  const extractedName = draft.assignee_name?.trim()
  const matchedUser = users.value.find(
    (user) => extractedName && (user.display_name === extractedName || user.username === extractedName),
  )
  assigneeId.value = matchedUser ? String(matchedUser.id) : ''
}

watch(
  () => props.draft,
  (draft) => {
    applyDraftAssignee(draft)
    dueDate.value = draft.due_date ?? ''
    title.value = draft.description.slice(0, 80)
    description.value = draft.description
  },
)

watch(users, () => applyDraftAssignee(props.draft))

onMounted(async () => {
  try {
    const response = await api.get<User[]>('/users/assignees')
    users.value = response.data
  } catch {
    users.value = []
  }
})

async function confirmDraft() {
  error.value = ''
  const parsedAssigneeId = Number(assigneeId.value)
  if (!Number.isInteger(parsedAssigneeId) || parsedAssigneeId <= 0) {
    error.value = '请选择负责人'
    return
  }

  loading.value = true
  try {
    await api.post(`/todo-drafts/${props.draft.id}/confirm`, {
      title: title.value,
      description: description.value,
      assignee_id: parsedAssigneeId,
      due_date: dueDate.value || null,
    })
    emit('confirmed')
  } catch {
    error.value = '确认待办失败'
  } finally {
    loading.value = false
  }
}

async function discardDraft() {
  error.value = ''
  loading.value = true
  try {
    await api.post(`/todo-drafts/${props.draft.id}/discard`)
    emit('discarded')
  } catch {
    error.value = '丢弃待办失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <article class="draft-card">
    <div class="draft-card-header">
      <strong>{{ draft.assignee_name || '未识别负责人' }}</strong>
      <span class="muted">置信度 {{ draft.confidence ?? '-' }}</span>
    </div>
    <p>{{ draft.source_sentence || draft.description }}</p>
    <div class="grid two">
      <label class="field">
        <span>标题</span>
        <input v-model="title" class="input" />
      </label>
      <label class="field">
        <span>负责人</span>
        <select v-model="assigneeId" class="input" data-test="assignee-select">
          <option value="">请选择负责人</option>
          <option v-for="user in users" :key="user.id" :value="String(user.id)">
            {{ userLabel(user) }}
          </option>
        </select>
      </label>
      <label class="field">
        <span>截止日期</span>
        <input v-model="dueDate" class="input" type="date" />
      </label>
      <label class="field">
        <span>状态</span>
        <div class="input readonly" data-test="draft-status">{{ draftStatusLabel }}</div>
      </label>
    </div>
    <label class="field">
      <span>描述</span>
      <textarea v-model="description" class="textarea compact"></textarea>
    </label>
    <p v-if="error" class="error">{{ error }}</p>
    <div class="toolbar-actions">
      <button class="button" type="button" :disabled="loading || draft.status !== 'draft'" @click="confirmDraft">
        确认
      </button>
      <button class="button secondary" type="button" :disabled="loading || draft.status !== 'draft'" @click="discardDraft">
        丢弃
      </button>
    </div>
  </article>
</template>
