/**
 * URL Input component for pasting YouTube URLs
 */
import { useState } from 'react'

interface URLInputProps {
  onSubmit: (url: string) => void
  isLoading?: boolean
}

export function URLInput({ onSubmit, isLoading = false }: URLInputProps) {
  const [url, setUrl] = useState('')
  const [error, setError] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (!url.trim()) {
      setError('Please enter a URL')
      return
    }

    if (!isValidURL(url)) {
      setError('Please enter a valid YouTube URL')
      return
    }

    onSubmit(url)
    setUrl('')
  }

  const isValidURL = (str: string): boolean => {
    try {
      new URL(str)
      return str.includes('youtube.com') || str.includes('youtu.be')
    } catch {
      return false
    }
  }

  return (
    <div className="space-y-2">
      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          placeholder="Paste a YouTube URL (video, playlist, or channel)..."
          value={url}
          onChange={(e) => {
            setUrl(e.target.value)
            setError('')
          }}
          disabled={isLoading}
          className="flex-1 rounded border border-muted bg-card px-3 py-2 text-foreground placeholder-muted-foreground focus:border-primary focus:outline-none disabled:opacity-50"
        />
        <button
          type="submit"
          disabled={isLoading || !url.trim()}
          className="rounded bg-primary px-4 py-2 text-primary-foreground hover:bg-primary/90 disabled:opacity-50 font-medium transition"
        >
          {isLoading ? 'Loading...' : 'Extract'}
        </button>
      </form>
      {error && (
        <p className="text-sm text-destructive">{error}</p>
      )}
    </div>
  )
}
