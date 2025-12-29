/**
 * QueuePanel component for displaying the transcription job queue
 */
import { Job } from '../api'
import { JobCard } from './JobCard'

interface QueuePanelProps {
  jobs: Job[]
  isLoading?: boolean
}

export function QueuePanel({ jobs, isLoading = false }: QueuePanelProps) {
  const pendingCount = jobs.filter((j) => j.status === 'pending').length
  const processingCount = jobs.filter((j) => j.status === 'processing').length
  const completedCount = jobs.filter((j) => j.status === 'completed').length
  const failedCount = jobs.filter((j) => j.status === 'failed').length

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="h-4 bg-muted rounded w-1/3 animate-pulse" />
        <div className="grid gap-4 md:grid-cols-2">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-muted rounded animate-pulse" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Transcription Queue</h2>
        <div className="text-sm text-muted-foreground">
          {jobs.length} total
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        <div className="rounded border border-muted bg-card p-3">
          <div className="text-2xl font-bold text-primary">{pendingCount}</div>
          <div className="text-xs text-muted-foreground">Pending</div>
        </div>
        <div className="rounded border border-muted bg-card p-3">
          <div className="text-2xl font-bold text-primary">{processingCount}</div>
          <div className="text-xs text-muted-foreground">Processing</div>
        </div>
        <div className="rounded border border-muted bg-card p-3">
          <div className="text-2xl font-bold text-green-400">{completedCount}</div>
          <div className="text-xs text-muted-foreground">Completed</div>
        </div>
        <div className="rounded border border-muted bg-card p-3">
          <div className="text-2xl font-bold text-destructive">{failedCount}</div>
          <div className="text-xs text-muted-foreground">Failed</div>
        </div>
      </div>

      {jobs.length === 0 ? (
        <div className="text-center text-muted-foreground py-8 rounded border border-muted border-dashed">
          <p>No jobs in queue yet</p>
          <p className="text-xs">Extract videos to add them to the queue</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {jobs.map((job) => (
            <JobCard key={job.id} job={job} />
          ))}
        </div>
      )}
    </div>
  )
}
