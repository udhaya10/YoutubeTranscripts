/**
 * Breadcrumb navigation for Channel > Playlist > Video hierarchy
 * Allows drilling down and collapsing at each level
 */
import { Breadcrumb, BreadcrumbItem, BreadcrumbList, BreadcrumbSeparator } from '@/components/ui/breadcrumb'

interface BreadcrumbNode {
  id: string
  title: string
  type: 'channel' | 'playlist' | 'video'
}

interface BrowseBreadcrumbProps {
  path: BreadcrumbNode[]
  onNavigate: (level: number) => void
}

export function BrowseBreadcrumb({ path, onNavigate }: BrowseBreadcrumbProps) {
  if (path.length === 0) return null

  return (
    <div className="mb-6">
      <Breadcrumb>
        <BreadcrumbList>
          {path.map((node, index) => (
            <div key={node.id} className="flex items-center gap-2">
              <BreadcrumbItem>
                <button
                  onClick={() => onNavigate(index)}
                  className="hover:text-primary transition-colors text-sm font-medium"
                >
                  {node.type === 'channel' && '📺'}
                  {node.type === 'playlist' && '📂'}
                  {node.type === 'video' && '🎥'}
                  <span className="ml-2">{node.title}</span>
                </button>
              </BreadcrumbItem>
              {index < path.length - 1 && <BreadcrumbSeparator />}
            </div>
          ))}
        </BreadcrumbList>
      </Breadcrumb>
    </div>
  )
}
