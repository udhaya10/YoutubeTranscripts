/**
 * UrlInput component with real-time validation using shadcn/ui
 * Shows whether the URL is a Playlist, Video, or Channel
 */
import { useState, useCallback, useEffect } from 'react'
import { Textarea } from '@/components/ui/textarea'
import { Button } from '@/components/ui/button'
import { apiClient } from '../api'

interface URLInputProps {
  onSubmit: (url: string) => void
  isLoading?: boolean
}

type ValidationResult = 'none' | 'video' | 'playlist' | 'channel' | 'invalid' | 'loading'

export function URLInput({ onSubmit, isLoading = false }: URLInputProps) {
  const [url, setUrl] = useState('')
  const [validation, setValidation] = useState<ValidationResult>('none')
  const [validationTimer, setValidationTimer] = useState<NodeJS.Timeout | null>(null)

  const validateUrl = useCallback(async (inputUrl: string) => {
    if (!inputUrl.trim()) {
      setValidation('none')
      return
    }

    setValidation('loading')

    try {
      const result = await apiClient.extractURL(inputUrl)
      const typeMap: Record<string, ValidationResult> = {
        'video': 'video',
        'playlist': 'playlist',
        'channel': 'channel',
        'unknown': 'invalid'
      }
      setValidation(typeMap[result.type] || 'invalid')
    } catch (err) {
      setValidation('invalid')
    }
  }, [])

  const handleUrlChange = (value: string) => {
    setUrl(value)

    // Clear previous timer
    if (validationTimer) {
      clearTimeout(validationTimer)
    }

    // Debounce validation - only validate after user stops typing for 500ms
    const timer = setTimeout(() => validateUrl(value), 500)
    setValidationTimer(timer)
  }

  useEffect(() => {
    return () => {
      if (validationTimer) {
        clearTimeout(validationTimer)
      }
    }
  }, [validationTimer])

  const handleSubmit = () => {
    if (validation !== 'invalid' && validation !== 'loading' && validation !== 'none') {
      onSubmit(url)
      setUrl('')
      setValidation('none')
    }
  }

  const getValidationIcon = () => {
    switch (validation) {
      case 'loading':
        return '⏳'
      case 'video':
        return '✓'
      case 'playlist':
        return '✓'
      case 'channel':
        return '✓'
      case 'invalid':
        return '✗'
      default:
        return ''
    }
  }

  const getValidationText = () => {
    switch (validation) {
      case 'loading':
        return 'Validating...'
      case 'video':
        return 'Video'
      case 'playlist':
        return 'Playlist'
      case 'channel':
        return 'Channel'
      case 'invalid':
        return 'Invalid'
      default:
        return ''
    }
  }

  const getValidationColor = () => {
    switch (validation) {
      case 'loading':
        return 'text-amber-500'
      case 'video':
      case 'playlist':
      case 'channel':
        return 'text-green-500'
      case 'invalid':
        return 'text-red-500'
      default:
        return 'text-muted-foreground'
    }
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        <Textarea
          placeholder="Paste YouTube URL (video, playlist, or channel)..."
          value={url}
          onChange={(e) => handleUrlChange(e.target.value)}
          className="min-h-24 pr-32 resize-none"
          disabled={isLoading}
        />
        {validation !== 'none' && (
          <div className={`absolute right-4 top-4 text-sm font-medium ${getValidationColor()} text-center`}>
            <div className="text-2xl">{getValidationIcon()}</div>
            <div className="text-xs mt-1 whitespace-nowrap">{getValidationText()}</div>
          </div>
        )}
      </div>

      <Button
        onClick={handleSubmit}
        disabled={isLoading || validation === 'invalid' || validation === 'loading' || validation === 'none'}
        className="w-full"
        size="lg"
      >
        {isLoading ? 'Extracting...' : 'Extract Content'}
      </Button>
    </div>
  )
}
