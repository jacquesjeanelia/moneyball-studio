import { motion } from 'framer-motion'

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div className="mb-4 grid h-16 w-16 place-items-center rounded-2xl surface text-signal-400">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 9v4M12 17h.01" strokeLinecap="round" />
          <path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z" strokeLinejoin="round" />
        </svg>
      </div>
      <h3 className="font-display font-bold text-xl text-chalk mb-1.5">Something went wrong</h3>
      <p className="text-chalk-dim max-w-sm mb-5">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="rounded-lg accent-bar px-5 py-2.5 text-sm font-bold text-white shadow-glow hover:brightness-110 transition"
        >
          Try again
        </button>
      )}
    </div>
  )
}

export function EmptyState({ title, hint }: { title: string; hint?: string }) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="flex flex-col items-center justify-center py-24 text-center"
    >
      <div className="mb-4 grid h-16 w-16 place-items-center rounded-2xl surface text-chalk-faint">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" strokeLinecap="round" />
        </svg>
      </div>
      <h3 className="font-display font-bold text-xl text-chalk mb-1.5">{title}</h3>
      {hint && <p className="text-chalk-dim max-w-sm">{hint}</p>}
    </motion.div>
  )
}

export function CardSkeleton() {
  return (
    <div className="rounded-card surface overflow-hidden">
      <div className="aspect-[4/5] skeleton" />
      <div className="px-3 py-3 space-y-2">
        <div className="h-2.5 w-2/3 rounded skeleton" />
        <div className="h-3.5 w-4/5 rounded skeleton" />
      </div>
    </div>
  )
}

export function GridSkeleton({ count = 18 }: { count?: number }) {
  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-3 sm:gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  )
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-10 text-chalk-faint">
      <span className="h-5 w-5 rounded-full border-2 border-ink-600 border-t-signal-500 animate-spin" />
      {label && <span className="text-sm">{label}</span>}
    </div>
  )
}
