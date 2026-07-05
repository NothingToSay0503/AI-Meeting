<script setup lang="ts">
type Status = 'todo' | 'doing' | 'done' | 'pending' | 'processing' | 'succeeded' | 'failed' | 'draft' | 'ready'

defineProps<{ status: Status }>()

const labels: Record<Status, string> = {
  todo: '待开始',
  doing: '进行中',
  done: '已完成',
  pending: '等待中',
  processing: '处理中',
  succeeded: '已成功',
  failed: '失败',
  draft: '待确认',
  ready: '已就绪',
}
</script>

<template>
  <span class="status-badge" :data-status="status">{{ labels[status] }}</span>
</template>
