/**
 * API client for communicating with the backend
 */

const API_BASE_URL = (typeof window !== 'undefined' && (window as any).REACT_APP_API_URL) || 'http://localhost:8000/api'

export interface HealthResponse {
  status: string
  service: string
  version: string
}

export interface Job {
  id: string
  video_id: string
  video_title?: string
  playlist_id?: string
  channel_id?: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  progress: number
  created_at: string
  started_at?: string
  completed_at?: string
  error_message?: string
  retry_count: number
  output_paths?: Record<string, string>
  metadata?: Record<string, any>
}

export interface URLExtractionResult {
  type: 'video' | 'playlist' | 'channel' | 'unknown'
  id: string
  title?: string
  metadata?: Record<string, any>
}

class APIClient {
  private baseUrl: string

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
  }

  async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({}))
      throw new Error(error.detail || `API error: ${response.status}`)
    }

    return response.json()
  }

  // Health check
  async getHealth(): Promise<HealthResponse> {
    return this.request('/health')
  }

  // Job management
  async createJob(
    video_id: string,
    video_title?: string,
    playlist_id?: string,
    channel_id?: string,
    metadata?: Record<string, any>
  ): Promise<Job> {
    return this.request('/jobs', {
      method: 'POST',
      body: JSON.stringify({
        video_id,
        video_title,
        playlist_id,
        channel_id,
        metadata,
      }),
    })
  }

  async getJob(jobId: string): Promise<Job> {
    return this.request(`/jobs/${jobId}`)
  }

  async listJobs(status?: string): Promise<Job[]> {
    const params = status ? `?status=${status}` : ''
    return this.request(`/jobs${params}`)
  }

  async updateJobStatus(
    jobId: string,
    status: string,
    progress?: number
  ): Promise<Job> {
    return this.request(`/jobs/${jobId}`, {
      method: 'PATCH',
      body: JSON.stringify({ status, progress }),
    })
  }

  // URL extraction
  async extractURL(url: string): Promise<URLExtractionResult> {
    return this.request('/extract/url', {
      method: 'POST',
      body: JSON.stringify({ url }),
    })
  }

  // WebSocket for real-time updates
  connectWebSocket(
    onMessage: (data: any) => void,
    onError?: (error: Event) => void
  ): WebSocket {
    const wsUrl = this.baseUrl
      .replace('http://', 'ws://')
      .replace('https://', 'wss://')
    const ws = new WebSocket(wsUrl)

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        onMessage(data)
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e)
      }
    }

    if (onError) {
      ws.onerror = onError
    }

    return ws
  }
}

export const apiClient = new APIClient()
