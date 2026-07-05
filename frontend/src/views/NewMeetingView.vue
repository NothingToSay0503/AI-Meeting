<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api } from '../api/client'

type CreateResponse = { meeting_id: number }
type InputMode = 'text' | 'audio'

const router = useRouter()
const mode = ref<InputMode>('text')
const title = ref('')
const transcript = ref('')
const audioFile = ref<File | null>(null)
const error = ref('')
const loading = ref(false)

function onFileChange(event: Event) {
  const input = event.target as HTMLInputElement
  audioFile.value = input.files?.[0] ?? null
}

async function submitMeeting() {
  error.value = ''
  loading.value = true
  try {
    let response
    if (mode.value === 'text') {
      response = await api.post<CreateResponse>('/meetings/manual-transcripts', {
        meeting_title: title.value,
        transcript_content: transcript.value,
      })
    } else {
      if (!audioFile.value) {
        error.value = '请选择 MP3 文件'
        return
      }
      const form = new FormData()
      form.append('meeting_title', title.value)
      form.append('file', audioFile.value)
      response = await api.post<CreateResponse>('/meetings/audio', form)
    }
    router.push(`/meetings/${response.data.meeting_id}`)
  } catch {
    error.value = '创建会议失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="page">
    <div class="toolbar">
      <div>
        <h1>新建会议</h1>
        <p class="muted">上传 MP3 或粘贴转写文本。</p>
      </div>
    </div>

    <form class="panel form-stack" @submit.prevent="submitMeeting">
      <label class="field">
        <span>会议标题</span>
        <input v-model="title" class="input" required />
      </label>

      <div class="segmented">
        <button type="button" :class="{ active: mode === 'text' }" @click="mode = 'text'">粘贴文本</button>
        <button type="button" :class="{ active: mode === 'audio' }" @click="mode = 'audio'">上传 MP3</button>
      </div>

      <label v-if="mode === 'text'" class="field">
        <span>会议原始文字记录</span>
        <textarea v-model="transcript" class="textarea" required></textarea>
      </label>

      <label v-else class="field">
        <span>会议录音</span>
        <input class="input" type="file" accept=".mp3,audio/mpeg" required @change="onFileChange" />
      </label>

      <p v-if="error" class="error">{{ error }}</p>
      <div class="toolbar-actions">
        <button class="button" type="submit" :disabled="loading">{{ loading ? '提交中' : '提交' }}</button>
        <RouterLink class="button secondary" to="/meetings">返回</RouterLink>
      </div>
    </form>
  </main>
</template>
