<script setup lang="ts">
import type { TaskStatus } from '../api/types'

defineProps<{ modelValue: TaskStatus | '' }>()
defineEmits<{ 'update:modelValue': [value: TaskStatus | ''] }>()

const tabs: Array<{ value: TaskStatus | ''; label: string }> = [
  { value: '', label: '全部' },
  { value: 'todo', label: '待开始' },
  { value: 'doing', label: '进行中' },
  { value: 'done', label: '已完成' },
]
</script>

<template>
  <div class="tabs">
    <button
      v-for="tab in tabs"
      :key="tab.value || 'all'"
      type="button"
      :class="{ active: modelValue === tab.value }"
      @click="$emit('update:modelValue', tab.value)"
    >
      {{ tab.label }}
    </button>
  </div>
</template>
