/**
 * QueuePanel component for displaying the transcription job queue
 */
import { useState } from 'react'
import { Job } from '../api'
import { JobCard } from './JobCard'

interface QueuePanelProps {
  jobs: Job[]
  isLoading?: boolean
  onRefresh?: () => void
  onJobUpdate?: (jobId: string, status: string) => void
}

type FilterStatus = 'all' | 'pending' | 'processing' | 'completed' | 'failed'

export function QueuePanel({ jobs, isLoading = false, onRefresh, onJobUpdate }: QueuePanelProps) {
  const [filterStatus, setFilterStatus] = useState<FilterStatus>('all')
  const [sortBy, setSortBy] = useState<'newest' | 'oldest' | 'progress'>('newest')

  const pendingCount = jobs.filter((j) => j.status === 'pending').length
  const processingCount = jobs.filter((j) => j.status === 'processing').length
  const completedCount = jobs.filter((j) => j.status === 'completed').length
  const failedCount = jobs.filter((j) => j.status === 'failed').length

  // Filter jobs by status
  const filteredJobs = filterStatus === 'all'
    ? jobs
    : jobs.filter((j) => j.status === filterStatus)

  // Sort jobs
  const sortedJobs = [...filteredJobs].sort((a, b) => {
    if (sortBy === 'newest') {
      return new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
    } else if (sortBy === 'oldest') {
      return new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
    } else {
      return b.progress - a.progress
    }
  })

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
        <div className="flex items-center gap-3">
          <div className="text-sm text-muted-foreground">
            {jobs.length} total
          </div>
          {onRefresh && (
            <button
              onClick={onRefresh}
              className="text-xs px-2 py-1 rounded border border-muted hover:bg-muted transition"
            >
              🔄 Refresh
            </button>
          )}
        </div>
      </div>

      {/* Stats Grid */}
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

      {/* Filter and Sort Controls */}
      {jobs.length > 0 && (
        <div className="flex items-center gap-3 flex-wrap p-3 rounded border border-muted bg-card/50">
          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-muted-foreground">Filter:</label>
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as FilterStatus)}
              className="text-xs px-2 py-1 rounded border border-muted bg-background text-foreground"
            >
              <option value="all">All Jobs</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="completed">Completed</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <label className="text-xs font-medium text-muted-foreground">Sort:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as 'newest' | 'oldest' | 'progress')}
              className="text-xs px-2 py-1 rounded border border-muted bg-background text-foreground"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="progress">By Progress</option>
            </select>
          </div>
        </div>
      )}

      {/* Jobs Grid */}
      {jobs.length === 0 ? (
        <div className="text-center text-muted-foreground py-8 rounded border border-muted border-dashed">
          <p>No jobs in queue yet</p>
          <p className="text-xs">Extract videos to add them to the queue</p>
        </div>
      ) : sortedJobs.length === 0 ? (
        <div className="text-center text-muted-foreground py-8 rounded border border-muted border-dashed">
          <p>No jobs match the selected filter</p>
          <p className="text-xs">Try selecting a different status</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sortedJobs.map((job) => (
            <JobCard
              key={job.id}
              job={job}
              onStatusChange={onJobUpdate}
            />
          ))}
        </div>
      )}
    </div>
  )
}
