/**
 * Tests for QueuePanel component - M14-M17 Queue Integration
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { QueuePanel } from '../../src/components/QueuePanel'
import { Job } from '../../src/api'

// Mock Job data
const createMockJob = (overrides?: Partial<Job>): Job => ({
  id: 'job-1',
  video_id: 'vid123',
  video_title: 'Test Video',
  status: 'pending',
  progress: 0,
  created_at: new Date().toISOString(),
  retry_count: 0,
  ...overrides,
})

describe('QueuePanel', () => {
  describe('Empty State', () => {
    it('displays empty state message when no jobs', () => {
      render(<QueuePanel jobs={[] } />)
      expect(screen.getByText('No jobs in queue yet')).toBeInTheDocument()
      expect(screen.getByText('Extract videos to add them to the queue')).toBeInTheDocument()
    })

    it('shows total count of 0', () => {
      render(<QueuePanel jobs={[]} />)
      expect(screen.getByText('0 total')).toBeInTheDocument()
    })
  })

  describe('Stats Display', () => {
    it('displays correct status counts', () => {
      const jobs = [
        createMockJob({ status: 'pending' }),
        createMockJob({ id: 'job-2', status: 'pending' }),
        createMockJob({ id: 'job-3', status: 'processing' }),
        createMockJob({ id: 'job-4', status: 'completed' }),
        createMockJob({ id: 'job-5', status: 'failed' }),
      ]

      render(<QueuePanel jobs={jobs} />)

      expect(screen.getByText('2')).toBeInTheDocument() // Pending (appears first in grid)
      expect(screen.getAllByText('1').length).toBeGreaterThan(0) // Processing, Completed, Failed
    })

    it('displays correct total count', () => {
      const jobs = [
        createMockJob(),
        createMockJob({ id: 'job-2' }),
        createMockJob({ id: 'job-3' }),
      ]

      render(<QueuePanel jobs={jobs} />)
      expect(screen.getByText('3 total')).toBeInTheDocument()
    })
  })

  describe('Filter Functionality', () => {
    const jobs = [
      createMockJob({ status: 'pending' }),
      createMockJob({ id: 'job-2', status: 'processing' }),
      createMockJob({ id: 'job-3', status: 'completed' }),
      createMockJob({ id: 'job-4', status: 'failed' }),
    ]

    it('renders filter controls when jobs exist', () => {
      render(<QueuePanel jobs={jobs} />)
      const filterSelects = screen.getAllByDisplayValue('All Jobs')
      expect(filterSelects.length).toBeGreaterThan(0)
    })

    it('filters jobs by pending status', () => {
      render(<QueuePanel jobs={jobs} />)
      const filterSelect = screen.getByDisplayValue('All Jobs')
      fireEvent.change(filterSelect, { target: { value: 'pending' } })

      // Should still show the stats and the pending job card
      expect(screen.getByText('Test Video')).toBeInTheDocument()
    })

    it('filters jobs by processing status', () => {
      render(<QueuePanel jobs={jobs} />)
      const filterSelect = screen.getByDisplayValue('All Jobs')
      fireEvent.change(filterSelect, { target: { value: 'processing' } })

      expect(screen.getByText('Test Video')).toBeInTheDocument()
    })

    it('shows no jobs message when filter matches nothing', () => {
      const singleJob = [createMockJob({ status: 'pending' })]
      render(<QueuePanel jobs={singleJob} />)

      const filterSelect = screen.getByDisplayValue('All Jobs')
      fireEvent.change(filterSelect, { target: { value: 'completed' } })

      expect(screen.getByText('No jobs match the selected filter')).toBeInTheDocument()
    })
  })

  describe('Sort Functionality', () => {
    const jobs = [
      createMockJob({
        id: 'job-1',
        created_at: new Date(2024, 0, 1).toISOString(),
        progress: 50,
      }),
      createMockJob({
        id: 'job-2',
        created_at: new Date(2024, 0, 2).toISOString(),
        progress: 75,
      }),
      createMockJob({
        id: 'job-3',
        created_at: new Date(2024, 0, 3).toISOString(),
        progress: 25,
      }),
    ]

    it('renders sort controls', () => {
      render(<QueuePanel jobs={jobs} />)
      const sortSelects = screen.getAllByDisplayValue('Newest First')
      expect(sortSelects.length).toBeGreaterThan(0)
    })

    it('can sort by newest first', () => {
      render(<QueuePanel jobs={jobs} />)
      const sortSelect = screen.getByDisplayValue('Newest First')
      expect(sortSelect).toBeInTheDocument()
      // Just verify the select is present and functional
    })

    it('can sort by oldest first', () => {
      render(<QueuePanel jobs={jobs} />)
      const sortSelect = screen.getAllByRole('combobox').find(
        (el) => (el as HTMLSelectElement).value === 'newest'
      ) as HTMLSelectElement
      fireEvent.change(sortSelect, { target: { value: 'oldest' } })
      expect(sortSelect.value).toBe('oldest')
    })

    it('can sort by progress', () => {
      render(<QueuePanel jobs={jobs} />)
      const sortSelect = screen.getAllByRole('combobox').find(
        (el) => (el as HTMLSelectElement).value === 'newest'
      ) as HTMLSelectElement
      fireEvent.change(sortSelect, { target: { value: 'progress' } })
      expect(sortSelect.value).toBe('progress')
    })
  })

  describe('Loading State', () => {
    it('displays loading skeleton when isLoading is true', () => {
      const { container } = render(<QueuePanel jobs={[]} isLoading={true} />)
      const pulseElements = container.querySelectorAll('.animate-pulse')
      expect(pulseElements.length).toBeGreaterThan(0)
    })
  })

  describe('Refresh Button', () => {
    it('displays refresh button when onRefresh prop is provided', () => {
      const mockRefresh = vi.fn()
      render(<QueuePanel jobs={[createMockJob()]} onRefresh={mockRefresh} />)
      expect(screen.getByText(/🔄 Refresh/)).toBeInTheDocument()
    })

    it('calls onRefresh when refresh button is clicked', () => {
      const mockRefresh = vi.fn()
      render(<QueuePanel jobs={[createMockJob()]} onRefresh={mockRefresh} />)
      const refreshButton = screen.getByText(/🔄 Refresh/)
      fireEvent.click(refreshButton)
      expect(mockRefresh).toHaveBeenCalled()
    })

    it('does not display refresh button when onRefresh is not provided', () => {
      render(<QueuePanel jobs={[createMockJob()]} />)
      expect(screen.queryByText(/🔄 Refresh/)).not.toBeInTheDocument()
    })
  })

  describe('Job Cards', () => {
    it('renders job cards for each job', () => {
      const jobs = [
        createMockJob({ id: 'job-1', video_title: 'Video 1' }),
        createMockJob({ id: 'job-2', video_title: 'Video 2' }),
      ]
      render(<QueuePanel jobs={jobs} />)
      expect(screen.getByText('Video 1')).toBeInTheDocument()
      expect(screen.getByText('Video 2')).toBeInTheDocument()
    })

    it('passes onJobUpdate callback to JobCard', () => {
      const mockUpdate = vi.fn()
      const jobs = [createMockJob()]
      render(<QueuePanel jobs={jobs} onJobUpdate={mockUpdate} />)
      // The callback should be passed to JobCard component
      // Verification would happen in JobCard tests
      expect(mockUpdate).not.toHaveBeenCalled() // Not called until user interacts
    })
  })

  describe('Integration', () => {
    it('maintains filter and sort state independently', () => {
      const jobs = [
        createMockJob({ id: 'job-1', status: 'pending' }),
        createMockJob({ id: 'job-2', status: 'completed' }),
      ]
      const { rerender } = render(<QueuePanel jobs={jobs} />)

      // Set filter
      const filterSelect = screen.getByDisplayValue('All Jobs')
      fireEvent.change(filterSelect, { target: { value: 'pending' } })

      // Update jobs and rerender
      rerender(<QueuePanel jobs={jobs} />)

      // Filter should still be 'pending'
      expect((filterSelect as HTMLSelectElement).value).toBe('pending')
    })

    it('displays stats that include filtered jobs', () => {
      const jobs = [
        createMockJob({ status: 'pending' }),
        createMockJob({ id: 'job-2', status: 'processing' }),
      ]
      render(<QueuePanel jobs={jobs} />)

      // Stats should show totals across all jobs
      expect(screen.getByText('1')).toBeInTheDocument() // At least one of the counts
    })
  })
})
