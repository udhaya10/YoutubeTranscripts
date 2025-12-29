/**
 * Main App component - YouTube Knowledge Base Web Application
 */
import { useState, useEffect, useCallback } from 'react'
import { Header } from './components/Header'
import { URLInput } from './components/URLInput'
import { MetadataTree } from './components/MetadataTree'
import { QueuePanel } from './components/QueuePanel'
import { useQueueWebSocket } from './hooks/useQueueWebSocket'
import { apiClient, Job } from './api'

interface TreeNode {
  id: string
  type: 'channel' | 'playlist' | 'video'
  title: string
  count?: number
  children?: TreeNode[]
}

function App() {
  const [jobs, setJobs] = useState<Job[]>([])
  const [treeData, setTreeData] = useState<TreeNode | null>(null)
  const [selectedNodes, setSelectedNodes] = useState<string[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Handle real-time job updates from WebSocket (M19)
  const handleJobUpdate = useCallback((updatedJob: Job) => {
    setJobs((prevJobs) =>
      prevJobs.map((job) =>
        job.id === updatedJob.id ? updatedJob : job
      )
    )
  }, [])

  // Connect to WebSocket for real-time updates
  const { isConnected } = useQueueWebSocket(handleJobUpdate)

  // Load jobs on mount
  useEffect(() => {
    loadJobs()
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

  const handleJobUpdate = async (jobId: string, status: string) => {
    try {
      await apiClient.updateJobStatus(jobId, status)
      await loadJobs()
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to update job'
      setError(message)
      console.error('Job update error:', err)
    }
  }

  const handleURLSubmit = async (url: string) => {
    setIsLoading(true)
    setError(null)
    setTreeData(null)
    setSelectedNodes([])

    try {
      const result = await apiClient.extractURL(url)

      // Build tree structure based on result type
      const tree = buildTreeFromResult(result)
      setTreeData(tree)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to extract URL'
      setError(message)
      console.error('URL extraction error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  const buildTreeFromResult = (result: any): TreeNode => {
    // This is a placeholder implementation
    // In real usage, this would construct the tree based on API response
    return {
      id: result.id,
      type: result.type,
      title: result.title || 'Unknown',
      count: result.metadata?.count,
      children: [],
    }
  }

  const handleAddToQueue = async () => {
    if (selectedNodes.length === 0) {
      setError('Please select at least one video')
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      // Create jobs for selected videos
      for (const videoId of selectedNodes) {
        await apiClient.createJob(videoId)
      }

      // Reload jobs
      await loadJobs()
      setSelectedNodes([])

      // Show success feedback
      console.log(`Added ${selectedNodes.length} videos to queue`)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to add to queue'
      setError(message)
      console.error('Add to queue error:', err)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-background text-foreground">
      <Header />

      <main className="container mx-auto px-4 py-6 space-y-8 max-w-6xl">
        {error && (
          <div className="rounded border border-destructive/30 bg-destructive/10 p-3 text-destructive text-sm">
            {error}
            <button
              onClick={() => setError(null)}
              className="float-right font-semibold hover:underline"
            >
              ✕
            </button>
          </div>
        )}

        {/* URL Input Section */}
        <section className="space-y-4">
          <div>
            <h2 className="text-lg font-semibold mb-2">Extract Content</h2>
            <p className="text-sm text-muted-foreground mb-4">
              Paste any YouTube URL (video, playlist, or channel) to get started
            </p>
          </div>
          <URLInput onSubmit={handleURLSubmit} isLoading={isLoading} />
        </section>

        {/* Metadata Tree Section */}
        {treeData && (
          <section className="space-y-4">
            <div>
              <h2 className="text-lg font-semibold mb-2">Browse Content</h2>
              <p className="text-sm text-muted-foreground mb-4">
                Select the videos you want to transcribe
              </p>
            </div>
            <MetadataTree
              data={treeData}
              isLoading={isLoading}
              onSelectNodes={setSelectedNodes}
            />

            {selectedNodes.length > 0 && (
              <div className="flex items-center gap-3 rounded border border-primary/30 bg-primary/10 p-4">
                <div className="flex-1">
                  <p className="text-sm font-medium">
                    {selectedNodes.length} video{selectedNodes.length !== 1 ? 's' : ''} selected
                  </p>
                </div>
                <button
                  onClick={handleAddToQueue}
                  disabled={isLoading}
                  className="rounded bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50 font-medium transition"
                >
                  {isLoading ? 'Adding...' : 'Add to Queue'}
                </button>
              </div>
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
          <QueuePanel
            jobs={jobs}
            isLoading={isLoading}
            onRefresh={loadJobs}
            onJobUpdate={handleJobUpdate}
          />
        </section>
      </main>

      <footer className="border-t border-muted bg-card mt-12 py-4">
        <div className="container mx-auto px-4 text-center text-xs text-muted-foreground">
          <p>YouTube Knowledge Base v0.1.0 • All files are saved locally</p>
        </div>
      </footer>
    </div>
  )
}

export default App
