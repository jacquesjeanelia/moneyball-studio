import { cn, categoryColor } from '@/lib/format'

/**
 * Position chip. `position` is the specific role shown as the label (e.g. "CM"),
 * while `category` (Attack/Midfield/Defender) drives the colour.
 */
export function PositionPill({
  position,
  category,
  className,
}: {
  position: string | null
  category?: string | null
  className?: string
}) {
  if (!position) return null
  const color = categoryColor(category)
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[11px] font-bold uppercase tracking-wider',
        className,
      )}
      style={{ color, background: `color-mix(in srgb, ${color} 14%, transparent)` }}
    >
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: color }} />
      {position}
    </span>
  )
}

/** Horizontal percentile bar (0–100) with colour ramp. `text` overrides the leading label. */
export function StatBar({ value, label, text }: { value: number; label?: string; text?: string }) {
  const color =
    value >= 80 ? 'var(--color-emerald)' : value >= 55 ? 'var(--color-volt)' : value >= 30 ? 'var(--color-amber)' : 'var(--color-signal-400)'
  return (
    <div className="flex items-center gap-2 w-full">
      {(text ?? label) && (
        <span className="text-xs text-chalk-faint w-14 shrink-0 tnum text-right whitespace-nowrap">{text ?? value}</span>
      )}
      <div className="relative h-1.5 flex-1 rounded-full bg-ink-700 overflow-hidden">
        <div
          className="absolute inset-y-0 left-0 rounded-full transition-[width] duration-700 ease-out"
          style={{ width: `${value}%`, background: color }}
        />
      </div>
    </div>
  )
}
