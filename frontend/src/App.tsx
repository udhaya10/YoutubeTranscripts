/**
 * Main App component - YouTube Knowledge Base Web Application
 * M26: Refactored with new shadcn/ui components and redesigned UI
 */
import { useState, useEffect, useCallback } from 'react'
import { Header } from './components/Header'
import { URLInput } from './components/URLInput'
import { BrowseBreadcrumb } from './components/BrowseBreadcrumb'
import { BrowseTable } from './components/BrowseTable'
import { QueueTable } from './components/QueueTable'
import { MetadataDisplay } from './components/MetadataDisplay'
import { TranscriptViewer } from './components/TranscriptViewer'
import { useQueueWebSocket } from './hooks/useQueueWebSocket'
import { apiClient, Job } from './api'

interface TreeNode {
  id: string
  type: 'channel' | 'playlist' | 'video'
  title: string
  count?: number
  children?: TreeNode[]
  uploader?: string
  duration?: number
  description?: string
}

interface BreadcrumbItem {
  id: string
  title: string
  type: 'channel' | 'playlist' | 'video'
  data?: any
}

function App() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [currentData, setCurrentData] = useState<TreeNode | null>(null)
  const [breadcrumbPath, setBreadcrumbPath] = useState<BreadcrumbItem[]>([])
  const [currentItems, setCurrentItems] = useState<any[]>([])
  const [selectedBrowseItems, setSelectedBrowseItems] = useState<string[]>([])
  const [selectedQueueJobs, setSelectedQueueJobs] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [viewingJobId, setViewingJobId] = useState<string | null>(null)

  // WebSocket for real-time job updates
  const handleJobUpdateFromWebSocket = useCallback((updatedJob: Job) => {
    setJobs((prevJobs) =>
      prevJobs.map((job) =>
        job.id === updatedJob.id ? updatedJob : job
      )
    )
  }, [])

  const { isConnected } = useQueueWebSocket(handleJobUpdateFromWebSocket)

  // Load jobs on mount and polling
  useEffect(() => {
    loadJobs()
    const pollInterval = setInterval(loadJobs, 3000)
    return () => clearInterval(pollInterval)
  }, [])

  const loadJobs = async () => {
    try {
      const result = await apiClient.listJobs()
      setJobs(result.jobs)
    } catch (err) {
      console.error('Failed to load jobs:', err)
      setError(err instanceof Error ? err.message : 'Failed to load jobs')
    }
  }

  const buildTreeFromResult = (result: any): TreeNode => {
    const buildNode = (item: any, itemType: 'channel' | 'playlist' | 'video'): TreeNode => ({
      id: item.id || item.channel_id || item.playlist_id || item.video_id,
      type: itemType,
      title: item.title || item.name || item.video_title || 'Unknown',
      count: item.video_count || item.count,
      uploader: item.uploader || item.channel_name,
      duration: item.duration,
      description: item.description,
      children:
        (itemType === 'channel' && item.playlists?.map((p: any) => buildNode(p, 'playlist'))) ||
        (itemType === 'playlist' && item.videos?.map((v: any) => buildNode(v, 'video'))) ||
        [],
    })
    return buildNode(result, result.type)
  }

  const handleURLSubmit = async (url: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const result = await apiClient.extractURL(url)
      const tree = buildTreeFromResult(result)
      setCurrentData(tree)
      setBreadcrumbPath([{ id: tree.id, title: tree.title, type: tree.type, data: tree }])
      setCurrentItems(tree.children || (tree.type === 'video' ? [tree] : []))
      setSelectedBrowseItems([])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to extract URL'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleBreadcrumbNavigate = (level: number) => {
    const newPath = breadcrumbPath.slice(0, level + 1)
    setBreadcrumbPath(newPath)
    const current = newPath[newPath.length - 1]?.data
    setCurrentItems(current?.children || (current?.type === 'video' ? [current] : []))
    setSelectedBrowseItems([])
  }

  const handleDrill = (itemId: string) => {
    const item = currentItems.find((i) => i.id === itemId)
    if (!item) return
    const newPath = [...breadcrumbPath, { id: item.id, title: item.title, type: item.type, data: item }]
    setBreadcrumbPath(newPath)
    setCurrentItems(item.children || (item.type === 'video' ? [item] : []))
    setSelectedBrowseItems([])
  }

  const handleAddToQueue = async () => {
    if (selectedBrowseItems.length === 0) {
      setError('Please select at least one video')
      return
    }
    setIsLoading(true)
    try {
      for (const itemId of selectedBrowseItems) {
        const item = currentItems.find((i) => i.id === itemId)
        if (item?.type === 'video') {
          await apiClient.createJob(itemId, item.title)
        }
      }
      await loadJobs()
      setSelectedBrowseItems([])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to add to queue'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteBrowseItem = (itemId: string) => {
    // Remove from current items display (local state only)
    setCurrentItems((prev) => prev.filter((item) => item.id !== itemId))
    setSelectedBrowseItems((prev) => prev.filter((id) => id !== itemId))
  }

  const handleDeleteJob = async (jobId: string) => {
    setIsLoading(true)
    try {
      await apiClient.deleteJob(jobId)
      // Reload jobs to reflect deletion
      await loadJobs()
      setSelectedQueueJobs((prev) => prev.filter((id) => id !== jobId))
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete job'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleDeleteMultipleJobs = async (jobIds: string[]) => {
    setIsLoading(true)
    try {
      for (const jobId of jobIds) {
        await apiClient.deleteJob(jobId)
      }
      // Reload jobs to reflect deletions
      await loadJobs()
      setSelectedQueueJobs([])
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to delete jobs'
      setError(message)
    } finally {
      setIsLoading(false)
    }
  }

  const currentMetadata =
    breadcrumbPath.length > 0 ? breadcrumbPath[breadcrumbPath.length - 1]?.data : null

  const browseTableItems = currentItems.map((item) => ({
    id: item.id,
    title: item.title,
    type: item.type,
    duration: item.duration,
    channel: item.uploader,
    count: item.count,
  }))

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />

      <main className="container mx-auto px-4 py-6 space-y-8 max-w-6xl">
        {error && (
          <div className="rounded border border-destructive/30 bg-destructive/10 p-4 text-destructive text-sm flex justify-between items-start">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="font-semibold hover:underline">
              ✕
            </button>
          </div>
        )}

        {/* URL Input Section */}
        <section className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-2">Extract Content</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Paste any YouTube URL (video, playlist, or channel)
            </p>
          </div>
          <URLInput onSubmit={handleURLSubmit} isLoading={isLoading} />
        </section>

        {/* Browse Content Section */}
        {currentItems.length > 0 && (
          <section className="space-y-6">
            <div>
              <h2 className="text-lg font-semibold mb-4">Browse Content</h2>
              {breadcrumbPath.length > 0 && (
                <BrowseBreadcrumb path={breadcrumbPath} onNavigate={handleBreadcrumbNavigate} />
              )}
            </div>

            <BrowseTable
              items={browseTableItems}
              selectedItems={selectedBrowseItems}
              onSelectionChange={setSelectedBrowseItems}
              onAddToQueue={handleAddToQueue}
              onDrill={handleDrill}
              onDelete={handleDeleteBrowseItem}
              isLoading={isLoading}
            />

            {currentMetadata && (
              <MetadataDisplay
                title={currentMetadata.title}
                description={currentMetadata.description}
                uploader={currentMetadata.uploader}
                videoCount={currentMetadata.count}
                duration={currentMetadata.duration}
              />
            )}
          </section>
        )}

        {/* Queue Section */}
        <section className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-2">Processing Queue</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Videos are processed one at a time in the background
            </p>
          </div>
          <QueueTable
            jobs={jobs}
            selectedJobs={selectedQueueJobs}
            onSelectionChange={setSelectedQueueJobs}
            onDeleteSingle={handleDeleteJob}
            onDelete={handleDeleteMultipleJobs}
            onView={setViewingJobId}
            isLoading={isLoading}
          />
        </section>
      </main>

      {/* Transcript Viewer Modal */}
      {viewingJobId && (
        <TranscriptViewer
          jobId={viewingJobId}
          videoTitle={jobs.find((j) => j.id === viewingJobId)?.video_title || 'Transcript'}
          onClose={() => setViewingJobId(null)}
        />
      )}

      <footer className="border-t border-muted bg-card mt-12 py-4">
        <div className="container mx-auto px-4 text-center text-xs text-muted-foreground">
          <p>YouTube Knowledge Base v0.1.0 • Powered by WhisperX + shadcn/ui</p>
        </div>
      </footer>
    </div>
  )
}

export default App
