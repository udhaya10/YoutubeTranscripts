/**
 * React hook for WebSocket connection to queue job updates
 * Provides real-time job status and progress updates
 * Implements M19: WebSocket real-time updates
 */
import { useEffect, useRef, useState, useCallback } from 'react'
import { Job } from '../api'

/**
 * Hook for subscribing to real-time job queue updates via WebSocket
 *
 * @param onJobUpdate - Callback function called when a job is updated
 * @returns Object with isConnected status
 *
 * @example
 * const { isConnected } = useQueueWebSocket((job) => {
 *   setJobs(prevJobs => prevJobs.map(j => j.id === job.id ? job : j))
 * })
 */
export function useQueueWebSocket(onJobUpdate: (job: Job) => void) {
  const wsRef = useRef<WebSocket | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>()
  const onJobUpdateRef = useRef(onJobUpdate)

  // Update the callback ref when it changes (avoid recreating connection)
  useEffect(() => {
    onJobUpdateRef.current = onJobUpdate
  }, [onJobUpdate])

  useEffect(() => {
    const connect = () => {
      try {
        // Determine protocol based on current page (http -> ws, https -> wss)
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
        const wsUrl = `${protocol}//${window.location.host}/ws/queue`

        console.log(`[WebSocket] Connecting to ${wsUrl}`)

        const ws = new WebSocket(wsUrl)

        ws.onopen = () => {
          console.log('[WebSocket] Connected successfully')
          setIsConnected(true)
        }

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)

            if (data.type === 'job_update' && data.job) {
              // Call the callback with the updated job
              onJobUpdateRef.current(data.job)
            } else if (data.type === 'heartbeat') {
              // Heartbeat to keep connection alive
              console.debug('[WebSocket] Heartbeat received')
            }
          } catch (err) {
            console.error('[WebSocket] Failed to parse message:', err)
          }
        }

        ws.onerror = (error) => {
          console.error('[WebSocket] Connection error:', error)
          setIsConnected(false)
        }

        ws.onclose = () => {
          console.log('[WebSocket] Disconnected, reconnecting in 5s...')
          setIsConnected(false)

          // Auto-reconnect after 5 seconds
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current)
          }
          reconnectTimeoutRef.current = setTimeout(connect, 5000)
        }

        wsRef.current = ws
      } catch (err) {
        console.error('[WebSocket] Failed to establish connection:', err)
        setIsConnected(false)

        // Retry after 5 seconds
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current)
        }
        reconnectTimeoutRef.current = setTimeout(connect, 5000)
      }
    }

    // Establish connection on mount
    connect()

    // Cleanup on unmount
    return () => {
      // Cancel any pending reconnect timeout
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
      }

      // Close WebSocket connection
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }

      setIsConnected(false)
    }
  }, []) // Empty dependency array - only run on mount/unmount

  return { isConnected }
}
