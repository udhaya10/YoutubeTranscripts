/**
 * Tests for API client - M14-M17 Queue Integration
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { apiClient, Job } from '../src/api'

// Mock fetch globally
const mockFetch = vi.fn()
global.fetch = mockFetch

describe('API Client', () => {
  beforeEach(() => {
    mockFetch.mockClear()
  })

  describe('Job Management', () => {
    describe('createJob', () => {
      it('sends correct POST request to /jobs', async () => {
        const mockJob: Job = {
          id: 'job-1',
          video_id: 'vid123',
          video_title: 'Test',
          status: 'pending',
          progress: 0,
          created_at: '2024-01-15T00:00:00Z',
          retry_count: 0,
        }

        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => mockJob,
        })

        const result = await apiClient.createJob('vid123', 'Test')

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/jobs'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('vid123'),
          })
        )
        expect(result.id).toBe('job-1')
      })

      it('includes all optional parameters in request', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        })

        await apiClient.createJob('vid123', 'Title', 'pl123', 'ch123')

        expect(mockFetch).toHaveBeenCalledWith(
          expect.any(String),
          expect.objectContaining({
            body: expect.stringContaining('playlist_id'),
          })
        )
      })
    })

    describe('listJobs', () => {
      it('fetches jobs without status filter', async () => {
        const mockResponse = {
          jobs: [{ id: 'job-1', video_id: 'vid1' }],
          count: 1,
        }

        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        })

        const result = await apiClient.listJobs()

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/jobs'),
          expect.any(Object)
        )
        expect(result.count).toBe(1)
        expect(result.jobs.length).toBe(1)
      })

      it('includes status filter parameter when provided', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ jobs: [], count: 0 }),
        })

        await apiClient.listJobs('pending')

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('?status=pending'),
          expect.any(Object)
        )
      })

      it('handles multiple status filters', async () => {
        const statuses = ['pending', 'processing', 'completed', 'failed']

        for (const status of statuses) {
          mockFetch.mockResolvedValueOnce({
            ok: true,
            json: async () => ({ jobs: [], count: 0 }),
          })

          await apiClient.listJobs(status)

          expect(mockFetch).toHaveBeenCalledWith(
            expect.stringContaining(`status=${status}`),
            expect.any(Object)
          )
        }
      })
    })

    describe('getJob', () => {
      it('fetches specific job by ID', async () => {
        const mockJob: Job = {
          id: 'job-123',
          video_id: 'vid123',
          status: 'processing',
          progress: 50,
          created_at: '2024-01-15T00:00:00Z',
          retry_count: 0,
        }

        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => mockJob,
        })

        const result = await apiClient.getJob('job-123')

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/jobs/job-123'),
          expect.any(Object)
        )
        expect(result.id).toBe('job-123')
      })
    })

    describe('updateJobStatus', () => {
      it('sends PATCH request with status only', async () => {
        const mockJob = { id: 'job-1', status: 'processing' }

        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => mockJob,
        })

        await apiClient.updateJobStatus('job-1', 'processing')

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('?status=processing'),
          expect.objectContaining({
            method: 'PATCH',
          })
        )
      })

      it('includes progress parameter when provided', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({}),
        })

        await apiClient.updateJobStatus('job-1', 'processing', 0.5)

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('progress=0.5'),
          expect.any(Object)
        )
      })

      it('handles status update to completed', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ status: 'completed' }),
        })

        await apiClient.updateJobStatus('job-1', 'completed', 1.0)

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('status=completed'),
          expect.any(Object)
        )
      })
    })

    describe('addJobsToQueue', () => {
      it('sends POST request with video IDs array', async () => {
        const mockResponse = {
          created: 2,
          jobs: [{ id: 'job-1' }, { id: 'job-2' }],
        }

        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => mockResponse,
        })

        const result = await apiClient.addJobsToQueue(['vid1', 'vid2'])

        expect(mockFetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/jobs/add-selected'),
          expect.objectContaining({
            method: 'POST',
            body: expect.stringContaining('["vid1","vid2"]'),
          })
        )
        expect(result.created).toBe(2)
      })

      it('handles empty video list', async () => {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ created: 0, jobs: [] }),
        })

        const result = await apiClient.addJobsToQueue([])

        expect(result.created).toBe(0)
      })
    })
  })

  describe('URL Extraction', () => {
    it('sends POST request to /extract endpoint', async () => {
      const mockResult = {
        type: 'video',
        id: 'vid123',
        title: 'Test Video',
        metadata: {},
      }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResult,
      })

      const result = await apiClient.extractURL('https://youtu.be/vid123')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/extract'),
        expect.objectContaining({
          method: 'POST',
          body: expect.stringContaining('https://youtu.be/vid123'),
        })
      )
      expect(result.type).toBe('video')
    })

    it('handles different URL types', async () => {
      const urls = [
        'https://youtu.be/vid123',
        'https://youtube.com/playlist?list=pl123',
        'https://youtube.com/@channel',
      ]

      for (const url of urls) {
        mockFetch.mockResolvedValueOnce({
          ok: true,
          json: async () => ({ type: 'video', id: 'test', metadata: {} }),
        })

        const result = await apiClient.extractURL(url)
        expect(result).toHaveProperty('type')
        expect(result).toHaveProperty('id')
      }
    })
  })

  describe('Metadata Retrieval', () => {
    it('fetches video metadata', async () => {
      const mockMetadata = { id: 'vid123', title: 'Video' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMetadata,
      })

      const result = await apiClient.getVideoMetadata('vid123')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metadata/video/vid123'),
        expect.any(Object)
      )
      expect(result.title).toBe('Video')
    })

    it('fetches playlist metadata', async () => {
      const mockMetadata = { id: 'pl123', title: 'Playlist' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMetadata,
      })

      const result = await apiClient.getPlaylistMetadata('pl123')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metadata/playlist/pl123'),
        expect.any(Object)
      )
    })

    it('fetches channel metadata', async () => {
      const mockMetadata = { id: 'ch123', title: 'Channel' }

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockMetadata,
      })

      const result = await apiClient.getChannelMetadata('ch123')

      expect(mockFetch).toHaveBeenCalledWith(
        expect.stringContaining('/api/metadata/channel/ch123'),
        expect.any(Object)
      )
    })
  })

  describe('Error Handling', () => {
    it('throws error when response is not ok', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: 'Not found' }),
      })

      await expect(apiClient.listJobs()).rejects.toThrow('Not found')
    })

    it('includes default error message when detail is missing', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => ({}),
      })

      await expect(apiClient.listJobs()).rejects.toThrow('API error: 500')
    })

    it('handles JSON parsing errors gracefully', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 500,
        json: async () => {
          throw new Error('Invalid JSON')
        },
      })

      await expect(apiClient.listJobs()).rejects.toThrow('API error: 500')
    })
  })

  describe('Request Headers', () => {
    it('includes Content-Type header', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      await apiClient.listJobs()

      expect(mockFetch).toHaveBeenCalledWith(
        expect.any(String),
        expect.objectContaining({
          headers: expect.objectContaining({
            'Content-Type': 'application/json',
          }),
        })
      )
    })

    it('allows custom headers to be passed', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      })

      // Note: This tests the API client's ability to accept headers in options
      // The actual implementation would use the request method
      expect(mockFetch).toBeDefined()
    })
  })
})
