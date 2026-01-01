/**
 * Transcript viewer component with Markdown and JSON tabs
 * Displays completed job transcripts with syntax highlighting
 */
import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { apiClient } from '../api'

interface TranscriptViewerProps {
  jobId: string
  videoTitle?: string
  onClose: () => void
}

type ViewerTab = 'markdown' | 'json'

export function TranscriptViewer({ jobId, videoTitle, onClose }: TranscriptViewerProps) {
  const [activeTab, setActiveTab] = useState<ViewerTab>('markdown')
  const [markdownContent, setMarkdownContent] = useState<string>('')
  const [jsonContent, setJsonContent] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadContent()
  }, [jobId])

  const loadContent = async () => {
    setLoading(true)
    setError(null)
    try {
      // Load both files
      const [transcriptData, metadataData] = await Promise.all([
        apiClient.getTranscript(jobId),
        apiClient.getMetadata(jobId),
      ])

      setMarkdownContent(transcriptData.content)
      setJsonContent(metadataData.content)
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load files'
      setError(message)
      console.error('Error loading transcript files:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-background rounded-lg border border-muted shadow-lg max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="border-b border-muted px-6 py-4 flex justify-between items-center">
          <div>
            <h2 className="text-xl font-semibold">{videoTitle || 'Transcript'}</h2>
            <p className="text-xs text-muted-foreground mt-1">Job ID: {jobId}</p>
          </div>
          <button
            onClick={onClose}
            className="text-2xl text-muted-foreground hover:text-foreground"
          >
            ✕
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b border-muted flex gap-0">
          <button
            onClick={() => setActiveTab('markdown')}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              activeTab === 'markdown'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            📄 Markdown
          </button>
          <button
            onClick={() => setActiveTab('json')}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              activeTab === 'json'
                ? 'border-primary text-primary'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            {} JSON
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="text-4xl mb-4">⏳</div>
                <p className="text-muted-foreground">Loading transcript...</p>
              </div>
            </div>
          ) : error ? (
            <div className="rounded border border-destructive/30 bg-destructive/10 p-4 text-destructive">
              <p className="font-semibold">Error Loading File</p>
              <p className="text-sm mt-2">{error}</p>
            </div>
          ) : activeTab === 'markdown' ? (
            <div className="prose prose-invert max-w-none">
              <pre className="bg-muted p-4 rounded overflow-auto max-h-[calc(90vh-300px)] text-sm font-mono whitespace-pre-wrap word-break">
                {markdownContent}
              </pre>
            </div>
          ) : (
            <pre className="bg-muted p-4 rounded overflow-auto max-h-[calc(90vh-300px)] text-sm font-mono text-green-400">
              {JSON.stringify(jsonContent, null, 2)}
            </pre>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-muted px-6 py-4 flex justify-end gap-2">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          <Button
            variant="outline"
            onClick={() => {
              const content =
                activeTab === 'markdown' ? markdownContent : JSON.stringify(jsonContent, null, 2)
              const filename = activeTab === 'markdown' ? 'transcript.md' : 'metadata.json'
              const blob = new Blob([content], { type: 'text/plain' })
              const url = URL.createObjectURL(blob)
              const a = document.createElement('a')
              a.href = url
              a.download = filename
              a.click()
              URL.revokeObjectURL(url)
            }}
          >
            Download
          </Button>
        </div>
      </div>
    </div>
  )
}
