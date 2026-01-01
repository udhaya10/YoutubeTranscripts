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

  // Render diagnostic
  const buttonDisabled = isLoading || validation === 'invalid' || validation === 'loading' || validation === 'none'
  console.log('[URLInput] RENDER - validation:', validation, 'url:', url, 'isLoading:', isLoading, 'buttonDisabled:', buttonDisabled)
  console.log('[URLInput] onSubmit callback:', typeof onSubmit, onSubmit ? 'defined' : 'UNDEFINED!')

  const validateUrl = useCallback(async (inputUrl: string) => {
    console.log('[URLInput] Starting validation for:', inputUrl)
    if (!inputUrl.trim()) {
      console.log('[URLInput] Input empty, setting validation to none')
      setValidation('none')
      return
    }

    console.log('[URLInput] Setting validation to loading')
    setValidation('loading')

    try {
      console.log('[URLInput] Making API call to extract URL:', inputUrl)
      const result = await apiClient.extractURL(inputUrl)
      console.log('[URLInput] ✓ API response successful:', result)
      console.log('[URLInput] API result.type:', result.type)

      const typeMap: Record<string, ValidationResult> = {
        'video': 'video',
        'playlist': 'playlist',
        'channel': 'channel',
        'unknown': 'invalid'
      }
      const newValidation = typeMap[result.type] || 'invalid'
      console.log('[URLInput] Mapped type "' + result.type + '" to validation "' + newValidation + '"')
      console.log('[URLInput] Calling setValidation with:', newValidation)
      setValidation(newValidation)
      console.log('[URLInput] ✓ setValidation called')
    } catch (err) {
      console.error('[URLInput] ✗ API error during validation:', err)
      console.log('[URLInput] Error message:', err instanceof Error ? err.message : String(err))
      setValidation('invalid')
    }
  }, [])

  const handleUrlChange = (value: string) => {
    console.log('[URLInput] handleUrlChange - new value:', value)
    setUrl(value)

    // Clear previous timer
    if (validationTimer) {
      console.log('[URLInput] Clearing previous validation timer')
      clearTimeout(validationTimer)
    }

    // Debounce validation - only validate after user stops typing for 500ms
    console.log('[URLInput] Setting validation timer for 500ms')
    const timer = setTimeout(() => {
      console.log('[URLInput] Timer fired! Calling validateUrl')
      validateUrl(value)
    }, 500)
    setValidationTimer(timer)
  }

  useEffect(() => {
    return () => {
      if (validationTimer) {
        clearTimeout(validationTimer)
      }
    }
  }, [validationTimer])

  // Log validation state changes
  useEffect(() => {
    console.log('[URLInput] Validation state changed:', validation)
  }, [validation])

  // Log URL changes
  useEffect(() => {
    console.log('[URLInput] URL changed:', url)
  }, [url])

  // Log isLoading changes
  useEffect(() => {
    console.log('[URLInput] isLoading changed:', isLoading)
  }, [isLoading])

  const handleSubmit = () => {
    console.log('[URLInput] ===== SUBMIT BUTTON CLICKED =====')
    console.log('[URLInput] Validation state:', validation)
    console.log('[URLInput] URL value:', url)
    console.log('[URLInput] isLoading prop:', isLoading)

    const isValidationValid = validation !== 'invalid' && validation !== 'loading' && validation !== 'none'
    const isUrlValid = url.trim().length > 0

    console.log('[URLInput] Is validation valid:', isValidationValid)
    console.log('[URLInput] Is URL valid:', isUrlValid)
    console.log('[URLInput] Will proceed with submission:', isValidationValid && isUrlValid)

    if (isValidationValid && isUrlValid) {
      console.log('[URLInput] ✓ Conditions met, calling onSubmit callback with URL:', url)
      try {
        onSubmit(url)
        console.log('[URLInput] ✓ onSubmit callback executed successfully')
      } catch (error) {
        console.error('[URLInput] ✗ Error in onSubmit callback:', error)
      }

      // Clear after submission starts
      setTimeout(() => {
        console.log('[URLInput] Clearing URL and validation state')
        setUrl('')
        setValidation('none')
      }, 100)
    } else {
      console.log('[URLInput] ✗ Conditions NOT met - submission blocked')
      console.log('[URLInput] Reason:', {
        validation_not_valid: !isValidationValid ? `validation=${validation}` : 'OK',
        url_not_valid: !isUrlValid ? 'URL is empty or whitespace only' : 'OK'
      })
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
        onClick={() => {
          console.log('[URLInput] ⭐ BUTTON CLICKED! isLoading:', isLoading, 'validation:', validation, 'url:', url)
          alert('[DEBUG] Button clicked! Check console for details.')
          handleSubmit()
        }}
        disabled={buttonDisabled}
        className="w-full"
        size="lg"
        style={{opacity: buttonDisabled ? 0.5 : 1, cursor: buttonDisabled ? 'not-allowed' : 'pointer'}}
      >
        {isLoading ? 'Extracting...' : 'Extract Content'}
      </Button>
    </div>
  )
}
