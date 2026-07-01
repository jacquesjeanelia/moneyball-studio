import { useEffect, useRef, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Category } from '@/api/types'
import type { Facets, FilterState, SortKey } from '@/hooks/useFilters'
import { SORT_OPTIONS } from '@/hooks/useFilters'
import { SmartImage } from './SmartImage'
import { cn, formatMarketValue, parsePriceInput, CATEGORY_COLORS } from '@/lib/format'

interface FilterBarProps {
  facets: Facets
  filters: FilterState
  onChange: (patch: Partial<FilterState>) => void
  onReset: () => void
  resultCount: number
  totalCount: number
}

// Broad-role labels for the segmented control (plural, user-facing).
const CATEGORY_LABELS: { key: Category; label: string }[] = [
  { key: 'Attack', label: 'Attackers' },
  { key: 'Midfield', label: 'Midfielders' },
  { key: 'Defender', label: 'Defenders' },
]

export function FilterBar({ facets, filters, onChange, onReset, resultCount, totalCount }: FilterBarProps) {
  const activeCount =
    (filters.category ? 1 : 0) +
    (filters.position ? 1 : 0) +
    (filters.leagueId ? 1 : 0) +
    (filters.countryId ? 1 : 0) +
    (filters.clubId ? 1 : 0) +
    (filters.maxPrice != null ? 1 : 0)

  return (
    <div className="space-y-3">
      {/* Category segmented control */}
      <SegmentedCategory value={filters.category} onChange={(c) => onChange({ category: c })} facets={facets} />

      {/* Futbin-style uniform filter fields */}
      <div className="flex flex-wrap items-stretch gap-2.5">
        <FacetField
          label="Position"
          options={facets.positions.map((p) => ({ id: p.key, name: p.key }))}
          value={filters.position}
          onChange={(v) => onChange({ position: v as string | null })}
        />
        <FacetField
          label="Nation"
          options={facets.countries.map((c) => ({ id: c.id, name: c.name, logo: c.logo }))}
          value={filters.countryId}
          onChange={(v) => onChange({ countryId: v as number | null })}
          searchable
          logoFit="cover"
        />
        <FacetField
          label="League"
          options={facets.leagues.map((l) => ({ id: l.id, name: l.name, logo: l.logo }))}
          value={filters.leagueId}
          // Switching league clears any club picked under the previous one.
          onChange={(v) => onChange({ leagueId: v as number | null, clubId: null })}
          searchable
        />
        <FacetField
          label="Club"
          options={facets.clubs
            .filter((c) => c.leagueId === filters.leagueId)
            .map((c) => ({ id: c.id, name: c.name, logo: c.logo }))}
          value={filters.clubId}
          onChange={(v) => onChange({ clubId: v as number | null })}
          searchable
          // Futbin-style: a league must be picked before clubs are selectable.
          disabled={filters.leagueId == null}
          disabledHint="Pick a league first"
        />
        <MaxPriceField value={filters.maxPrice} onChange={(v) => onChange({ maxPrice: v })} />

        <div className="ml-auto flex items-end gap-2.5">
          <SortDropdown value={filters.sort} onChange={(s) => onChange({ sort: s })} />
          {activeCount > 0 && (
            <button
              onClick={onReset}
              className="text-xs font-semibold text-chalk-faint hover:text-signal-400 transition-colors px-2 py-2.5"
            >
              Clear all ({activeCount})
            </button>
          )}
        </div>
      </div>

      <div className="text-sm text-chalk-faint">
        <span className="font-display font-bold text-chalk tnum">{resultCount.toLocaleString()}</span> of{' '}
        <span className="tnum">{totalCount.toLocaleString()}</span> players
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------

function SegmentedCategory({
  value,
  onChange,
  facets,
}: {
  value: Category | null
  onChange: (c: Category | null) => void
  facets: Facets
}) {
  const available = new Set(facets.categories.map((c) => c.key))
  const items: { key: Category | null; label: string }[] = [
    { key: null, label: 'All' },
    ...CATEGORY_LABELS.filter((c) => available.has(c.key)),
  ]
  return (
    <div className="inline-flex items-center rounded-lg surface p-0.5">
      {items.map((it) => {
        const active = value === it.key
        const color = it.key ? CATEGORY_COLORS[it.key] : 'var(--color-chalk)'
        return (
          <button
            key={it.label}
            onClick={() => onChange(it.key)}
            aria-pressed={active}
            className="relative px-3.5 py-1.5 text-sm font-semibold rounded-md transition-colors"
            style={{ color: active ? '#fff' : 'var(--color-chalk-dim)' }}
          >
            {active && (
              <motion.span
                layoutId="cat-pill"
                className="absolute inset-0 rounded-md"
                style={{ background: it.key ? `color-mix(in srgb, ${color} 30%, var(--color-ink-600))` : 'var(--color-ink-600)' }}
                transition={{ type: 'spring', stiffness: 400, damping: 32 }}
              />
            )}
            <span className="relative">{it.label}</span>
          </button>
        )
      })}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Uniform "field" shell: a small uppercase label sitting above the control,
// matching futbin's row of filter boxes. Used by every facet + the price box.

function FieldShell({
  label,
  active,
  children,
  innerRef,
  disabled = false,
}: {
  label: string
  active: boolean
  children: React.ReactNode
  innerRef?: React.Ref<HTMLDivElement>
  disabled?: boolean
}) {
  return (
    <div ref={innerRef} className="relative">
      <div
        className={cn(
          'flex flex-col rounded-lg surface px-3 py-1.5 min-w-[8.5rem] transition-colors hover:border-ink-500 focus-within:border-signal-500/60',
          active && 'border-signal-500/50',
          disabled && 'opacity-50',
        )}
      >
        <span className="text-[10px] font-bold uppercase tracking-wider text-chalk-faint leading-none mb-1">{label}</span>
        {children}
      </div>
    </div>
  )
}

interface FieldOpt {
  id: string | number
  name: string
  logo?: string | null
}

function FacetField({
  label,
  options,
  value,
  onChange,
  searchable = false,
  logoFit = 'contain',
  disabled = false,
  disabledHint,
}: {
  label: string
  options: FieldOpt[]
  value: string | number | null
  onChange: (v: string | number | null) => void
  searchable?: boolean
  logoFit?: 'cover' | 'contain'
  disabled?: boolean
  disabledHint?: string
}) {
  const [open, setOpen] = useState(false)
  const [q, setQ] = useState('')
  const ref = useRef<HTMLDivElement>(null)
  const selected = options.find((o) => o.id === value)
  useClickOutside(ref, () => setOpen(false))

  const filtered = searchable && q ? options.filter((o) => o.name.toLowerCase().includes(q.toLowerCase())) : options

  return (
    <FieldShell label={label} active={value != null} innerRef={ref} disabled={disabled}>
      <button
        onClick={() => !disabled && setOpen((o) => !o)}
        disabled={disabled}
        title={disabled ? disabledHint : undefined}
        aria-label={`${label} filter`}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={cn('flex items-center gap-2 text-sm font-semibold text-left', disabled && 'cursor-not-allowed')}
      >
        {selected?.logo && (
          <span className="h-4 w-5 shrink-0">
            <SmartImage src={selected.logo} alt="" fallback="hidden" fit={logoFit} className="h-full w-full" />
          </span>
        )}
        <span className={cn('flex-1 truncate max-w-[120px]', selected ? 'text-chalk' : 'text-chalk-dim')}>
          {disabled && disabledHint ? disabledHint : selected ? selected.name : `All ${label.toLowerCase()}s`}
        </span>
        <Chevron open={open} />
      </button>

      <AnimatePresence>
        {open && !disabled && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.16 }}
            className="absolute left-0 top-full z-40 mt-2 w-64 rounded-xl surface-raised shadow-card p-1.5 max-h-80 overflow-hidden flex flex-col"
          >
            {searchable && (
              <input
                autoFocus
                value={q}
                onChange={(e) => setQ(e.target.value)}
                placeholder={`Search ${label.toLowerCase()}…`}
                className="mb-1.5 w-full rounded-lg bg-ink-900 px-3 py-2 text-sm text-chalk placeholder:text-chalk-faint outline-none focus:ring-1 focus:ring-signal-500"
              />
            )}
            <div className="overflow-y-auto hide-scrollbar">
              <DropdownRow active={value === null} onClick={() => { onChange(null); setOpen(false); setQ('') }}>
                <span className="text-chalk-dim">All {label.toLowerCase()}s</span>
              </DropdownRow>
              {filtered.map((o) => (
                <DropdownRow key={o.id} active={value === o.id} onClick={() => { onChange(o.id); setOpen(false); setQ('') }}>
                  {o.logo && (
                    <span className="h-4 w-5 shrink-0">
                      <SmartImage src={o.logo} alt="" fallback="hidden" fit={logoFit} className="h-full w-full" />
                    </span>
                  )}
                  <span className="truncate flex-1">{o.name}</span>
                </DropdownRow>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </FieldShell>
  )
}

function DropdownRow({
  active,
  onClick,
  children,
}: {
  active: boolean
  onClick: () => void
  children: React.ReactNode
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        'flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-sm text-left transition-colors',
        active ? 'bg-signal-500/15 text-signal-400' : 'text-chalk hover:bg-ink-700',
      )}
    >
      {children}
    </button>
  )
}

// ---------------------------------------------------------------------------

// No player is worth more than this — caps whatever the user types.
const MAX_PRICE_EUR = 500_000_000

function MaxPriceField({ value, onChange }: { value: number | null; onChange: (v: number | null) => void }) {
  const [raw, setRaw] = useState('')

  useEffect(() => {
    if (value === null) setRaw('')
  }, [value])

  const commit = (s: string) => {
    setRaw(s)
    const parsed = parsePriceInput(s)
    onChange(parsed === null ? null : Math.min(parsed, MAX_PRICE_EUR))
  }

  return (
    <FieldShell label="Max price" active={value != null}>
      <div className="flex items-center gap-1 text-sm font-semibold">
        <span className="text-chalk-faint">€</span>
        <input
          inputMode="numeric"
          value={raw}
          onChange={(e) => commit(e.target.value)}
          placeholder="Any"
          title="In thousands — type 500 for €500K, or use m for millions (e.g. 30m)"
          className="w-12 bg-transparent text-chalk placeholder:text-chalk-dim outline-none tnum"
        />
        {/* <span className="text-chalk-faint">K</span> */}
        {value != null && (
          <span className="ml-1 text-xs text-volt font-bold tnum border-l border-ink-600 pl-1.5">{formatMarketValue(value)}</span>
        )}
      </div>
    </FieldShell>
  )
}

// ---------------------------------------------------------------------------

function SortDropdown({ value, onChange }: { value: SortKey; onChange: (s: SortKey) => void }) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)
  useClickOutside(ref, () => setOpen(false))
  const current = SORT_OPTIONS.find((o) => o.key === value)

  return (
    <div className="relative" ref={ref}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Sort players"
        aria-haspopup="listbox"
        aria-expanded={open}
        className="inline-flex items-center gap-2 rounded-lg surface px-3 py-2.5 text-sm font-semibold text-chalk-dim hover:border-ink-500 transition-colors"
      >
        <SortGlyph />
        <span className="hidden sm:inline">{current?.label}</span>
        <Chevron open={open} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: -6, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -6, scale: 0.98 }}
            transition={{ duration: 0.16 }}
            className="absolute right-0 z-40 mt-2 w-56 rounded-xl surface-raised shadow-card p-1.5 max-h-80 overflow-y-auto hide-scrollbar"
          >
            {SORT_OPTIONS.map((o) => (
              <DropdownRow key={o.key} active={o.key === value} onClick={() => { onChange(o.key); setOpen(false) }}>
                {o.label}
              </DropdownRow>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ---------------------------------------------------------------------------

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width="14"
      height="14"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      className={cn('transition-transform duration-200 text-chalk-faint shrink-0', open && 'rotate-180')}
    >
      <path d="m6 9 6 6 6-6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function SortGlyph() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M3 6h12M3 12h9M3 18h6" strokeLinecap="round" />
    </svg>
  )
}

function useClickOutside(ref: React.RefObject<HTMLElement | null>, handler: () => void) {
  useEffect(() => {
    function onDown(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) handler()
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [ref, handler])
}
