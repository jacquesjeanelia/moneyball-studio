import { useEffect, useRef, useState } from 'react'

interface SearchBarProps {
  value: string
  onChange: (v: string) => void
  resultCount: number
}

/**
 * As-you-type search. We debounce the upstream onChange slightly so typing
 * stays buttery while filtering ≈1760 rows; the input itself stays fully
 * controlled and responsive.
 */
export function SearchBar({ value, onChange, resultCount }: SearchBarProps) {
  const [local, setLocal] = useState(value)
  const ref = useRef<HTMLInputElement>(null)

  // keep local in sync if cleared externally
  useEffect(() => {
    setLocal(value)
  }, [value])

  useEffect(() => {
    // Only push upstream when the text actually changed. This avoids spurious
    // setSearchParams calls (whose stale closure could otherwise revert the URL
    // while navigating away during the page-exit animation).
    if (local === value) return
    const t = setTimeout(() => onChange(local), 90)
    return () => clearTimeout(t)
  }, [local, value, onChange])

  // // "/" focuses search
  // useEffect(() => {
  //   function onKey(e: KeyboardEvent) {
  //     if (e.key === '/' && document.activeElement?.tagName !== 'INPUT') {
  //       e.preventDefault()
  //       ref.current?.focus()
  //     }
  //   }
  //   window.addEventListener('keydown', onKey)
  //   return () => window.removeEventListener('keydown', onKey)
  // }, [])

  return (
    <div className="group relative">
      <div className="pointer-events-none absolute left-4 top-1/2 -translate-y-1/2 text-chalk-faint group-focus-within:text-signal-400 transition-colors">
        <SearchGlyph />
      </div>
      <input
        ref={ref}
        value={local}
        onChange={(e) => setLocal(e.target.value)}
        placeholder="Search for players..."
        className="w-full rounded-2xl surface pl-12 pr-28 py-4 text-base sm:text-lg font-medium text-chalk placeholder:text-chalk-faint outline-none transition-all focus:border-signal-500/60 focus:shadow-glow"
        aria-label="Search players"
      />
      <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
        {local ? (
          <button
            onClick={() => {
              setLocal('')
              ref.current?.focus()
            }}
            className="rounded-lg px-2 py-1 text-xs font-semibold text-chalk-faint hover:text-chalk hover:bg-ink-700 transition-colors"
          >
            Clear
          </button>
        ) : (
          <kbd className="hidden sm:inline-flex h-6 items-center rounded-md border border-ink-600 bg-ink-900 px-2 text-xs font-mono text-chalk-faint">
            /
          </kbd>
        )}
      </div>
      {local && (
        <span className="absolute -bottom-5 left-4 text-xs text-chalk-faint tnum">
          {resultCount.toLocaleString()} match{resultCount === 1 ? '' : 'es'}
        </span>
      )}
    </div>
  )
}

function SearchGlyph() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" strokeLinecap="round" />
    </svg>
  )
}
