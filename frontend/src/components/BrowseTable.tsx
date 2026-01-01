/**
 * Browse table for videos/playlists with checkboxes, progress, and actions
 * Shows extracted content with selection and queue options
 */
import { useState, useRef, useEffect } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Checkbox } from '@/components/ui/checkbox'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'

interface BrowseItem {
  id: string
  title: string
  duration?: number
  channel?: string
  count?: number // for playlists/channels
  type: 'video' | 'playlist' | 'channel'
}

interface BrowseTableProps {
  items: BrowseItem[]
  selectedItems: string[]
  onSelectionChange: (itemIds: string[]) => void
  onAddToQueue: (itemIds: string[]) => void
  onDrill?: (itemId: string) => void
  onDelete?: (itemId: string) => void
  isLoading?: boolean
}

export function BrowseTable({
  items,
  selectedItems,
  onSelectionChange,
  onAddToQueue,
  onDrill,
  onDelete,
  isLoading = false,
}: BrowseTableProps) {
  const [hoveredId, setHoveredId] = useState<string | null>(null)

  const allSelected = items.length > 0 && items.every((item) => selectedItems.includes(item.id))
  const someSelected = selectedItems.length > 0 && !allSelected
  const headerCheckboxRef = useRef<HTMLInputElement>(null)

  // Set indeterminate state for header checkbox
  useEffect(() => {
    if (headerCheckboxRef.current) {
      headerCheckboxRef.current.indeterminate = someSelected
    }
  }, [someSelected])

  const handleSelectAll = () => {
    if (allSelected) {
      onSelectionChange([])
    } else {
      onSelectionChange(items.map((item) => item.id))
    }
  }

  const handleSelectOne = (itemId: string) => {
    if (selectedItems.includes(itemId)) {
      onSelectionChange(selectedItems.filter((id) => id !== itemId))
    } else {
      onSelectionChange([...selectedItems, itemId])
    }
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  return (
    <div className="space-y-4">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">
              <Checkbox
                ref={headerCheckboxRef}
                checked={allSelected}
                onChange={handleSelectAll}
                disabled={isLoading}
              />
            </TableHead>
            <TableHead>Title</TableHead>
            <TableHead>Type</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Channel</TableHead>
            <TableHead className="text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((item) => (
            <TableRow
              key={item.id}
              onMouseEnter={() => setHoveredId(item.id)}
              onMouseLeave={() => setHoveredId(null)}
              className="hover:bg-muted/50"
            >
              <TableCell>
                <Checkbox
                  checked={selectedItems.includes(item.id)}
                  onChange={() => handleSelectOne(item.id)}
                  disabled={isLoading}
                />
              </TableCell>
              <TableCell className="font-medium max-w-xs truncate">{item.title}</TableCell>
              <TableCell>
                <span className="text-xs font-semibold px-2 py-1 rounded bg-muted">
                  {item.type === 'video' && '🎥'} {item.type}
                </span>
              </TableCell>
              <TableCell className="text-sm text-muted-foreground">
                {item.count ? `${item.count} videos` : formatDuration(item.duration)}
              </TableCell>
              <TableCell className="text-sm text-muted-foreground truncate max-w-xs">
                {item.channel || '-'}
              </TableCell>
              <TableCell className="text-right space-x-1">
                {item.type !== 'video' && onDrill && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onDrill(item.id)}
                    disabled={isLoading}
                    className="text-xs"
                  >
                    Explore
                  </Button>
                )}
                {item.type === 'video' && (
                  <Button
                    size="sm"
                    onClick={() => onAddToQueue([item.id])}
                    disabled={isLoading || selectedItems.includes(item.id)}
                    variant={selectedItems.includes(item.id) ? 'secondary' : 'default'}
                    className="text-xs"
                  >
                    {selectedItems.includes(item.id) ? '✓ Selected' : 'Add'}
                  </Button>
                )}
                {onDelete && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      if (confirm(`Delete "${item.title}"?`)) {
                        onDelete(item.id)
                      }
                    }}
                    disabled={isLoading}
                    className="text-xs text-destructive hover:text-destructive"
                  >
                    🗑️
                  </Button>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>

      {selectedItems.length > 0 && (
        <div className="flex items-center justify-between rounded border border-primary/30 bg-primary/10 p-4">
          <div className="text-sm font-medium">
            {selectedItems.length} video{selectedItems.length !== 1 ? 's' : ''} selected
          </div>
          <div className="space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSelectionChange([])}
              disabled={isLoading}
            >
              Clear
            </Button>
            <Button
              size="sm"
              onClick={() => onAddToQueue(selectedItems.filter((id) => {
                const item = items.find((i) => i.id === id)
                return item?.type === 'video'
              }))}
              disabled={isLoading}
            >
              Add All to Queue
            </Button>
          </div>
        </div>
      )}
    </div>
  )
}
