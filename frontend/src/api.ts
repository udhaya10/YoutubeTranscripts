/**
 * API client for communicating with the backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

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

  async listJobs(status?: string): Promise<{ jobs: Job[]; count: number }> {
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

  async addJobsToQueue(videoIds: string[]): Promise<{ created: number; jobs: Job[] }> {
    return this.request('/jobs/add-selected', {
      method: 'POST',
      body: JSON.stringify({ video_ids: videoIds }),
    })
  }

  async deleteJob(jobId: string): Promise<{ success: boolean }> {
    return this.request(`/jobs/${jobId}`, {
      method: 'DELETE',
    })
  }

  // URL extraction
  async extractURL(url: string): Promise<URLExtractionResult> {
    return this.request('/extract', {
      method: 'POST',
      body: JSON.stringify({ url }),
    })
  }

  // Metadata retrieval
  async getVideoMetadata(videoId: string): Promise<Record<string, any>> {
    return this.request(`/metadata/video/${videoId}`)
  }

  async getPlaylistMetadata(playlistId: string): Promise<Record<string, any>> {
    return this.request(`/metadata/playlist/${playlistId}`)
  }

  async getChannelMetadata(channelId: string): Promise<Record<string, any>> {
    return this.request(`/metadata/channel/${channelId}`)
  }

  // WebSocket for real-time updates
  connectWebSocket(
    onMessage: (data: any) => void,
    onError?: (error: Event) => void
  ): WebSocket {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws/queue`
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
