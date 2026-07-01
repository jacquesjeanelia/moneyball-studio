import { useEffect, useRef, useState } from 'react'

/**
 * Progressive rendering: reveal `step` more items whenever the sentinel
 * scrolls into view. Keeps initial paint fast even with ≈1760 results and
 * avoids a heavyweight virtualization dep for a grid of this size.
 */
export function useProgressiveList<T>(items: T[], step = 36, initial = 36) {
  const [count, setCount] = useState(initial)
  const sentinelRef = useRef<HTMLDivElement>(null)

  // reset when the underlying list identity changes (new filter/search)
  useEffect(() => {
    setCount(initial)
  }, [items, initial])

  useEffect(() => {
    const el = sentinelRef.current
    if (!el) return
    const obs = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) {
          setCount((c) => Math.min(c + step, items.length))
        }
      },
      { rootMargin: '600px 0px' },
    )
    obs.observe(el)
    return () => obs.disconnect()
  }, [items.length, step])

  return {
    visible: items.slice(0, count),
    hasMore: count < items.length,
    sentinelRef,
  }
}
