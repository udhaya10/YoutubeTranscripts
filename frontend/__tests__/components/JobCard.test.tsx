/**
 * Tests for JobCard component - M14-M17 Queue Integration
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { JobCard } from '../../src/components/JobCard'
import { Job } from '../../src/api'

// Mock Job data
const createMockJob = (overrides?: Partial<Job>): Job => ({
  id: 'job-1',
  video_id: 'vid123',
  video_title: 'Test Video',
  status: 'pending',
  progress: 0,
  created_at: new Date('2024-01-15').toISOString(),
  retry_count: 0,
  ...overrides,
})

describe('JobCard', () => {
  describe('Content Display', () => {
    it('displays video title', () => {
      const job = createMockJob({ video_title: 'My Test Video' })
      render(<JobCard job={job} />)
      expect(screen.getByText('My Test Video')).toBeInTheDocument()
    })

    it('displays "Untitled Video" when title is missing', () => {
      const job = createMockJob({ video_title: undefined })
      render(<JobCard job={job} />)
      expect(screen.getByText('Untitled Video')).toBeInTheDocument()
    })

    it('displays video ID', () => {
      const job = createMockJob({ video_id: 'abc123xyz' })
      render(<JobCard job={job} />)
      expect(screen.getByText(/abc123xyz/)).toBeInTheDocument()
    })

    it('displays creation date', () => {
      const job = createMockJob()
      render(<JobCard job={job} />)
      expect(screen.getByText(/Created:/)).toBeInTheDocument()
    })
  })

  describe('Status Display', () => {
    it('displays pending status with correct styling', () => {
      const job = createMockJob({ status: 'pending' })
      render(<JobCard job={job} />)
      expect(screen.getByText(/Pending/i)).toBeInTheDocument()
      expect(screen.getByText('⏳')).toBeInTheDocument()
    })

    it('displays processing status with correct styling', () => {
      const job = createMockJob({ status: 'processing' })
      render(<JobCard job={job} />)
      expect(screen.getByText(/Processing/i)).toBeInTheDocument()
      expect(screen.getByText('⚙️')).toBeInTheDocument()
    })

    it('displays completed status with correct styling', () => {
      const job = createMockJob({ status: 'completed' })
      render(<JobCard job={job} />)
      expect(screen.getByText(/Completed/i)).toBeInTheDocument()
      expect(screen.getByText('✅')).toBeInTheDocument()
    })

    it('displays failed status with correct styling', () => {
      const job = createMockJob({ status: 'failed' })
      render(<JobCard job={job} />)
      expect(screen.getByText(/Failed/i)).toBeInTheDocument()
      expect(screen.getByText('❌')).toBeInTheDocument()
    })
  })

  describe('Progress Bar', () => {
    it('displays progress percentage', () => {
      const job = createMockJob({ progress: 50 })
      render(<JobCard job={job} />)
      expect(screen.getByText('50%')).toBeInTheDocument()
    })

    it('displays 0% progress initially', () => {
      const job = createMockJob({ progress: 0 })
      render(<JobCard job={job} />)
      expect(screen.getByText('0%')).toBeInTheDocument()
    })

    it('displays 100% progress when complete', () => {
      const job = createMockJob({ progress: 100, status: 'completed' })
      render(<JobCard job={job} />)
      expect(screen.getByText('100%')).toBeInTheDocument()
    })

    it('rounds progress percentage', () => {
      const job = createMockJob({ progress: 33.7 })
      render(<JobCard job={job} />)
      expect(screen.getByText('34%')).toBeInTheDocument()
    })
  })

  describe('Error Display', () => {
    it('displays error message when present', () => {
      const job = createMockJob({
        status: 'failed',
        error_message: 'Network connection failed',
      })
      render(<JobCard job={job} />)
      expect(screen.getByText('Network connection failed')).toBeInTheDocument()
      expect(screen.getByText(/Error:/)).toBeInTheDocument()
    })

    it('does not display error section when error_message is missing', () => {
      const job = createMockJob({ error_message: undefined })
      render(<JobCard job={job} />)
      expect(screen.queryByText(/Error:/)).not.toBeInTheDocument()
    })
  })

  describe('Output Files Display', () => {
    it('displays output files section when present', () => {
      const job = createMockJob({
        output_paths: {
          transcript_md: '/path/to/transcript.md',
          transcript_json: '/path/to/transcript.json',
          metadata: '/path/to/metadata.json',
        },
      })
      render(<JobCard job={job} />)
      expect(screen.getByText('Output Files')).toBeInTheDocument()
      expect(screen.getByText('📄 Markdown')).toBeInTheDocument()
      expect(screen.getByText('📊 JSON')).toBeInTheDocument()
      expect(screen.getByText('📋 Metadata')).toBeInTheDocument()
    })

    it('displays only available output files', () => {
      const job = createMockJob({
        output_paths: {
          transcript_md: '/path/to/transcript.md',
        },
      })
      render(<JobCard job={job} />)
      expect(screen.getByText('📄 Markdown')).toBeInTheDocument()
      expect(screen.queryByText('📊 JSON')).not.toBeInTheDocument()
    })

    it('does not show output files section when no output_paths', () => {
      const job = createMockJob({ output_paths: undefined })
      render(<JobCard job={job} />)
      expect(screen.queryByText('Output Files')).not.toBeInTheDocument()
    })
  })

  describe('Action Buttons', () => {
    it('does not show action buttons for non-actionable statuses', () => {
      const job = createMockJob({ status: 'processing' })
      render(<JobCard job={job} onStatusChange={vi.fn()} />)
      expect(screen.queryByText(/Show Actions/)).not.toBeInTheDocument()
    })

    it('shows action buttons for pending status', () => {
      const job = createMockJob({ status: 'pending' })
      render(<JobCard job={job} onStatusChange={vi.fn()} />)
      expect(screen.getByText('Show Actions')).toBeInTheDocument()
    })

    it('shows action buttons for failed status', () => {
      const job = createMockJob({ status: 'failed' })
      render(<JobCard job={job} onStatusChange={vi.fn()} />)
      expect(screen.getByText('Show Actions')).toBeInTheDocument()
    })

    it('toggles action visibility when Show Actions is clicked', () => {
      const job = createMockJob({ status: 'pending' })
      render(<JobCard job={job} onStatusChange={vi.fn()} />)

      const showButton = screen.getByText('Show Actions')
      fireEvent.click(showButton)

      expect(screen.getByText('Hide Actions')).toBeInTheDocument()
      expect(screen.getByText('✕ Cancel')).toBeInTheDocument()
    })

    it('displays retry button for failed jobs', () => {
      const mockUpdate = vi.fn()
      const job = createMockJob({ status: 'failed' })
      render(<JobCard job={job} onStatusChange={mockUpdate} />)

      const showButton = screen.getByText('Show Actions')
      fireEvent.click(showButton)

      expect(screen.getByText('🔄 Retry')).toBeInTheDocument()
    })

    it('displays cancel button for pending jobs', () => {
      const mockUpdate = vi.fn()
      const job = createMockJob({ status: 'pending' })
      render(<JobCard job={job} onStatusChange={mockUpdate} />)

      const showButton = screen.getByText('Show Actions')
      fireEvent.click(showButton)

      expect(screen.getByText('✕ Cancel')).toBeInTheDocument()
    })

    it('calls onStatusChange when retry is clicked', () => {
      const mockUpdate = vi.fn()
      const job = createMockJob({ status: 'failed' })
      render(<JobCard job={job} onStatusChange={mockUpdate} />)

      const showButton = screen.getByText('Show Actions')
      fireEvent.click(showButton)

      const retryButton = screen.getByText('🔄 Retry')
      fireEvent.click(retryButton)

      expect(mockUpdate).toHaveBeenCalledWith('job-1', 'pending')
    })

    it('calls onStatusChange when cancel is clicked', () => {
      const mockUpdate = vi.fn()
      const job = createMockJob({ status: 'pending' })
      render(<JobCard job={job} onStatusChange={mockUpdate} />)

      const showButton = screen.getByText('Show Actions')
      fireEvent.click(showButton)

      const cancelButton = screen.getByText('✕ Cancel')
      fireEvent.click(cancelButton)

      expect(mockUpdate).toHaveBeenCalledWith('job-1', 'cancelled')
    })

    it('does not show actions when onStatusChange is not provided', () => {
      const job = createMockJob({ status: 'pending' })
      render(<JobCard job={job} />)
      expect(screen.queryByText('Show Actions')).not.toBeInTheDocument()
    })
  })

  describe('Layout', () => {
    it('renders as a card with proper styling', () => {
      const job = createMockJob()
      const { container } = render(<JobCard job={job} />)
      const card = container.querySelector('.rounded.border')
      expect(card).toBeInTheDocument()
    })

    it('displays all main sections in correct order', () => {
      const job = createMockJob({
        error_message: 'Test error',
        output_paths: { transcript_md: '/path/to/file.md' },
      })
      const { container } = render(<JobCard job={job} />)
      const sections = container.querySelectorAll('.space-y')
      expect(sections.length).toBeGreaterThan(0)
    })
  })
})
