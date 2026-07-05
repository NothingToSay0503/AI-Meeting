import type { AiJob, AsrJob, Meeting } from '../api/types'

export function shouldPollMeetingDetail(
  meeting: Meeting | null,
  aiJobs: AiJob[],
  asrJobs: AsrJob[],
) {
  if (meeting?.status === 'processing') {
    return true
  }
  return [...aiJobs, ...asrJobs].some((job) => job.status === 'pending' || job.status === 'processing')
}
