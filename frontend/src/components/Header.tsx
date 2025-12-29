/**
 * Header component with branding and navigation
 */

export function Header() {
  return (
    <header className="border-b border-muted bg-card">
      <div className="container mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-8 w-8 items-center justify-center rounded bg-primary text-primary-foreground font-bold">
              ▶
            </div>
            <div>
              <h1 className="text-lg font-semibold">YouTube Knowledge Base</h1>
              <p className="text-xs text-muted-foreground">Extract • Organize • Transcribe</p>
            </div>
          </div>
          <div className="text-sm text-muted-foreground">
            Version 0.1.0
          </div>
        </div>
      </div>
    </header>
  )
}
