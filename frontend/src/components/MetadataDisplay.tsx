/**
 * Display metadata for selected content
 * Shows thumbnail, description, channel info, etc.
 */

interface MetadataDisplayProps {
  title?: string
  description?: string
  uploader?: string
  videoCount?: number
  duration?: number
  thumbnail?: string
}

export function MetadataDisplay({
  title,
  description,
  uploader,
  videoCount,
  duration,
  thumbnail,
}: MetadataDisplayProps) {
  if (!title) {
    return (
      <div className="rounded border border-muted bg-card p-6 text-center text-muted-foreground">
        Select content to view metadata
      </div>
    )
  }

  const formatDuration = (seconds?: number) => {
    if (!seconds) return '-'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    if (hours > 0) return `${hours}h ${minutes}m`
    return `${minutes}m`
  }

  return (
    <div className="rounded border border-muted bg-card p-6 space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {thumbnail && (
          <div className="md:col-span-1">
            <img
              src={thumbnail}
              alt={title}
              className="w-full rounded border border-muted object-cover aspect-video"
            />
          </div>
        )}

        <div className={thumbnail ? 'md:col-span-2' : 'md:col-span-3'}>
          <h3 className="text-lg font-semibold mb-2">{title}</h3>

          {uploader && (
            <p className="text-sm text-muted-foreground mb-3">
              📺 <span className="font-medium text-foreground">{uploader}</span>
            </p>
          )}

          {description && (
            <div className="mb-4">
              <p className="text-sm text-muted-foreground font-medium mb-1">Description</p>
              <p className="text-sm text-foreground line-clamp-3">{description}</p>
            </div>
          )}

          <div className="flex gap-6 text-sm">
            {videoCount !== undefined && (
              <div>
                <span className="text-muted-foreground">Videos</span>
                <p className="font-semibold text-foreground">{videoCount}</p>
              </div>
            )}
            {duration !== undefined && (
              <div>
                <span className="text-muted-foreground">Duration</span>
                <p className="font-semibold text-foreground">{formatDuration(duration)}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
