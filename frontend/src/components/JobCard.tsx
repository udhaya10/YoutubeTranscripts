/**
 * JobCard component for displaying a single video transcription job
 */
import { useState } from 'react'
import { Job } from '../api'

interface JobCardProps {
  job: Job
  onStatusChange?: (jobId: string, status: string) => void
}

export function JobCard({ job, onStatusChange }: JobCardProps) {
  const [showActions, setShowActions] = useState(false)
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-muted text-muted-foreground'
      case 'processing':
        return 'bg-primary/20 text-primary'
      case 'completed':
        return 'bg-green-500/20 text-green-400'
      case 'failed':
        return 'bg-destructive/20 text-destructive'
      default:
        return 'bg-muted text-muted-foreground'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return '⏳'
      case 'processing':
        return '⚙️'
      case 'completed':
        return '✅'
      case 'failed':
        return '❌'
      default:
        return '❓'
    }
  }

  const formattedTime = new Date(job.created_at).toLocaleString()

  return (
    <div className="rounded border border-muted bg-card p-4 space-y-3">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-foreground truncate">
            {job.video_title || 'Untitled Video'}
          </h3>
          <p className="text-xs text-muted-foreground">
            ID: {job.video_id}
          </p>
        </div>
        <div className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap flex items-center gap-1 ${getStatusColor(job.status)}`}>
          <span>{getStatusIcon(job.status)}</span>
          <span className="capitalize">{job.status}</span>
        </div>
      </div>

      <div className="space-y-2">
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Progress</span>
          <span className="text-foreground font-medium">{Math.round(job.progress)}%</span>
        </div>
        <div className="w-full h-2 bg-muted rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div>
          <span className="text-muted-foreground">Created:</span>
          <p className="text-foreground">{formattedTime}</p>
        </div>
        {job.retry_count !== undefined && job.retry_count > 0 && (
          <div>
            <span className="text-muted-foreground">Retries:</span>
            <p className="text-foreground">{job.retry_count}/3</p>
          </div>
        )}
      </div>

      {/* Only show error box for failed jobs */}
      {job.error_message && job.status === 'failed' && (
        <div className="p-2 rounded bg-destructive/10 border border-destructive/30 space-y-1">
          <div className="flex items-center gap-2">
            <span className="text-destructive font-medium">⚠️ Error</span>
            {job.retry_count && job.retry_count < 3 && (
              <span className="text-xs text-destructive/80">(will retry)</span>
            )}
          </div>
          <p className="text-destructive text-xs leading-relaxed">{job.error_message}</p>
        </div>
      )}

      {job.output_paths && (
        <div className="pt-2 border-t border-muted space-y-1">
          <p className="text-xs text-muted-foreground font-medium">Output Files</p>
          <div className="flex flex-wrap gap-1">
            {job.output_paths.transcript_md && (
              <span className="text-xs bg-muted/50 px-2 py-1 rounded">📄 Markdown</span>
            )}
            {job.output_paths.transcript_json && (
              <span className="text-xs bg-muted/50 px-2 py-1 rounded">📊 JSON</span>
            )}
            {job.output_paths.metadata && (
              <span className="text-xs bg-muted/50 px-2 py-1 rounded">📋 Metadata</span>
            )}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {(job.status === 'pending' || job.status === 'failed') && onStatusChange && (
        <div className="pt-2 border-t border-muted space-y-2">
          <button
            onClick={() => setShowActions(!showActions)}
            className="w-full text-xs py-1 px-2 rounded border border-muted hover:bg-muted transition font-medium"
          >
            {showActions ? 'Hide Actions' : 'Show Actions'}
          </button>
          {showActions && (
            <div className="flex gap-2">
              {job.status === 'failed' && (
                <button
                  onClick={() => onStatusChange(job.id, 'pending')}
                  className="flex-1 text-xs py-1 px-2 rounded bg-primary/20 text-primary hover:bg-primary/30 transition font-medium"
                >
                  🔄 Retry
                </button>
              )}
              {job.status === 'pending' && (
                <button
                  onClick={() => onStatusChange(job.id, 'cancelled')}
                  className="flex-1 text-xs py-1 px-2 rounded bg-destructive/20 text-destructive hover:bg-destructive/30 transition font-medium"
                >
                  ✕ Cancel
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
