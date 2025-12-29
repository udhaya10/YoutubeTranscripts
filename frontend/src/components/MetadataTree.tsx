/**
 * MetadataTree component for displaying Channel → Playlist → Video hierarchy
 */
import { useState } from 'react'

interface TreeNode {
  id: string
  type: 'channel' | 'playlist' | 'video'
  title: string
  count?: number
  children?: TreeNode[]
  selected?: boolean
}

interface MetadataTreeProps {
  data: TreeNode | null
  isLoading?: boolean
  onSelectNodes?: (selectedIds: string[]) => void
}

export function MetadataTree({
  data,
  isLoading = false,
  onSelectNodes,
}: MetadataTreeProps) {
  const [expandedIds, setExpandedIds] = useState<Set<string>>(new Set())
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set())

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedIds)
    if (newExpanded.has(id)) {
      newExpanded.delete(id)
    } else {
      newExpanded.add(id)
    }
    setExpandedIds(newExpanded)
  }

  const toggleSelected = (id: string) => {
    const newSelected = new Set(selectedIds)
    if (newSelected.has(id)) {
      newSelected.delete(id)
    } else {
      newSelected.add(id)
    }
    setSelectedIds(newSelected)
    onSelectNodes?.(Array.from(newSelected))
  }

  const getIcon = (type: string) => {
    switch (type) {
      case 'channel':
        return '📺'
      case 'playlist':
        return '📋'
      case 'video':
        return '🎬'
      default:
        return '📁'
    }
  }

  const renderNode = (node: TreeNode, depth: number = 0): JSX.Element => {
    const isExpanded = expandedIds.has(node.id)
    const isSelected = selectedIds.has(node.id)
    const hasChildren = node.children && node.children.length > 0

    return (
      <div key={node.id} style={{ marginLeft: `${depth * 20}px` }}>
        <div className="flex items-center gap-2 py-1">
          {hasChildren && (
            <button
              onClick={() => toggleExpanded(node.id)}
              className="w-6 text-left hover:text-primary"
            >
              {isExpanded ? '▼' : '▶'}
            </button>
          )}
          {!hasChildren && <div className="w-6" />}

          {node.type !== 'video' && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => toggleSelected(node.id)}
              className="cursor-pointer"
            />
          )}
          {node.type === 'video' && <div className="w-4" />}

          <span className="text-lg">{getIcon(node.type)}</span>

          <div className="flex-1 cursor-pointer hover:text-primary" onClick={() => toggleExpanded(node.id)}>
            <span className="text-sm">{node.title}</span>
            {node.count !== undefined && (
              <span className="ml-2 text-xs text-muted-foreground">
                ({node.count})
              </span>
            )}
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div>
            {node.children!.map((child) => renderNode(child, depth + 1))}
          </div>
        )}
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="space-y-2 animate-pulse">
        <div className="h-4 bg-muted rounded w-1/3" />
        <div className="h-4 bg-muted rounded w-1/2" />
        <div className="h-4 bg-muted rounded w-1/4" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="text-center text-muted-foreground py-8">
        <p>Enter a YouTube URL to get started</p>
      </div>
    )
  }

  return (
    <div className="rounded border border-muted bg-card p-4 space-y-2">
      <div className="text-sm font-semibold text-muted-foreground mb-4">
        Metadata Structure
      </div>
      {renderNode(data)}
    </div>
  )
}
