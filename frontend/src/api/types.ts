export type User = {
  id: number
  username: string
  display_name: string
  email: string | null
  role: 'admin' | 'member'
  status: 'active' | 'disabled'
}

export type MeetingStatus = 'draft' | 'processing' | 'ready' | 'failed'
export type JobStatus = 'pending' | 'processing' | 'succeeded' | 'failed'
export type TaskStatus = 'todo' | 'doing' | 'done'
export type DraftStatus = 'draft' | 'confirmed' | 'discarded'

export type Meeting = {
  id: number
  title: string
  meeting_time: string
  source_type: 'audio' | 'manual_text'
  status: MeetingStatus
  created_by: number
}

export type Transcript = {
  id: number
  meeting_id: number
  source_type: 'audio_asr' | 'manual_text'
  content: string
  created_by: number
  created_at: string
}

export type AiJob = {
  id: number
  meeting_id: number
  transcript_id: number
  provider: string
  model: string
  status: JobStatus
  retry_count: number
  error_message: string | null
}

export type AsrJob = {
  id: number
  meeting_id: number
  audio_file_id: number
  provider: string
  model: string
  status: JobStatus
  error_message: string | null
  started_at: string | null
  finished_at: string | null
}

export type MeetingSummary = {
  id: number
  meeting_id: number
  ai_job_id: number
  topic: string
  participants_json: { items: string[] }
  key_points_json: { items: string[] }
  decisions_json: { items: string[] }
  raw_model_output: Record<string, unknown>
  created_at: string
}

export type TodoDraft = {
  id: number
  meeting_id: number
  ai_job_id: number
  description: string
  assignee_name: string | null
  assignee_id: number | null
  due_date: string | null
  source_sentence: string | null
  confidence: number | null
  status: DraftStatus
  confirmed_task_id: number | null
}

export type Task = {
  id: number
  meeting_id: number
  draft_id: number | null
  title: string
  description: string
  assignee_id: number
  due_date: string | null
  status: TaskStatus
  confirmed_by: number
  confirmed_at: string
}
