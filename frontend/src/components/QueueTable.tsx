/**
 * Queue table displaying processing, completed, and failed jobs
 * Shows progress bars, status, and bulk actions
 */
import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import { Job } from '../api'

interface QueueTableProps {
  jobs: Job[]
  selectedJobs: string[]
  onSelectionChange: (jobIds: string[]) => void
  onRetry?: (jobIds: string[]) => void
  onCancel?: (jobIds: string[]) => void
  onDelete?: (jobIds: string[]) => void
  isLoading?: boolean
}

export function QueueTable({
  jobs,
  selectedJobs,
  onSelectionChange,
  onRetry,
  onCancel,
  onDelete,
  isLoading = false,
}: QueueTableProps) {
  const allSelected = jobs.length > 0 && jobs.every((job) => selectedJobs.includes(job.id))
  const someSelected = selectedJobs.length > 0 && !allSelected

  const handleSelectAll = () => {
    if (allSelected) {
      onSelectionChange([])
    } else {
      onSelectionChange(jobs.map((job) => job.id))
    }
  }

  const handleSelectOne = (jobId: string) => {
    if (selectedJobs.includes(jobId)) {
      onSelectionChange(selectedJobs.filter((id) => id !== jobId))
    } else {
      onSelectionChange([...selectedJobs, jobId])
    }
  }

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

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return '-'
    return new Date(dateStr).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  if (jobs.length === 0) {
    return (
      <div className="rounded border border-muted bg-card p-8 text-center text-muted-foreground">
        No jobs in queue
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                checked={allSelected}
                ref={(element) => {
                  if (element && someSelected) {
                    element.indeterminate = true
                  }
                }}
                onChange={handleSelectAll}
                disabled={isLoading}
              />
            </TableHead>
            <TableHead>Title</TableHead>
            <TableHead className="w-24">Status</TableHead>
            <TableHead className="w-32">Progress</TableHead>
            <TableHead className="w-40">Created</TableHead>
            <TableHead className="text-right w-32">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {jobs.map((job) => (
            <TableRow key={job.id} className="hover:bg-muted/50">
              <TableCell>
                <Checkbox
                  checked={selectedJobs.includes(job.id)}
                  onChange={() => handleSelectOne(job.id)}
                  disabled={isLoading}
                />
              </TableCell>
              <TableCell className="font-medium max-w-xs truncate">
                {job.video_title || 'Untitled'}
              </TableCell>
              <TableCell>
                <div className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${getStatusColor(job.status)}`}>
                  <span>{getStatusIcon(job.status)}</span>
                  <span className="capitalize">{job.status}</span>
                </div>
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress value={job.progress} className="h-2 w-16" />
                  <span className="text-xs font-medium w-8">{Math.round(job.progress)}%</span>
                </div>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {formatDate(job.created_at)}
              </TableCell>
              <TableCell className="text-right space-x-1">
                {job.status === 'failed' && onRetry && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onRetry([job.id])}
                    disabled={isLoading}
                    className="text-xs"
                  >
                    Retry
                  </Button>
                )}
                {job.status === 'processing' && onCancel && (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onCancel([job.id])}
                    disabled={isLoading}
                    className="text-xs"
                  >
                    Cancel
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selectedJobs.length > 0 && (
        <div className="flex items-center justify-between rounded border border-primary/30 bg-primary/10 p-4">
          <div className="text-sm font-medium">
            {selectedJobs.length} job{selectedJobs.length !== 1 ? 's' : ''} selected
          </div>
          <div className="space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSelectionChange([])}
              disabled={isLoading}
            >
              Clear
            </Button>
            {onRetry && (
              <Button
                size="sm"
                onClick={() => onRetry(selectedJobs)}
                disabled={isLoading}
              >
                Retry Selected
              </Button>
            )}
            {onDelete && (
              <Button
                size="sm"
                variant="destructive"
                onClick={() => onDelete(selectedJobs)}
                disabled={isLoading}
              >
                Delete Selected
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
