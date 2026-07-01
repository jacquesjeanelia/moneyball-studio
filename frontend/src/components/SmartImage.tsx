import { useState } from 'react'
import { cn, colorFromString, initials } from '@/lib/format'

interface SmartImageProps {
  src: string | null | undefined
  alt: string
  className?: string
  /** For player photos: show initials avatar on failure. */
  fallback?: 'initials' | 'icon' | 'hidden'
  fallbackName?: string
  imgClassName?: string
  /** How the image fills its box. 'contain' avoids cropping (flags, logos). */
  fit?: 'cover' | 'contain'
}

/**
 * Image with graceful fallback. We're confident the URLs resolve, but if a
 * remote asset 404s or a network hiccup occurs, we degrade to an initials
 * avatar (players) or a neutral glyph (logos) instead of a broken image.
 */
export function SmartImage({
  src,
  alt,
  className,
  fallback = 'initials',
  fallbackName,
  imgClassName,
  fit = 'cover',
}: SmartImageProps) {
  const [failed, setFailed] = useState(false)
  const [loaded, setLoaded] = useState(false)

  const showFallback = !src || failed

  if (showFallback && fallback === 'hidden') return null

  if (showFallback) {
    const name = fallbackName ?? alt
    if (fallback === 'icon') {
      return (
        <div className={cn('flex items-center justify-center bg-ink-700 text-chalk-faint', className)} aria-label={alt}>
          <ShieldGlyph />
        </div>
      )
    }
    return (
      <div
        className={cn('flex items-center justify-center font-display font-bold text-chalk select-none', className)}
        style={{ background: colorFromString(name) }}
        aria-label={alt}
      >
        {initials(name)}
      </div>
    )
  }

  return (
    <div className={cn('relative overflow-hidden', className)}>
      {!loaded && <div className="absolute inset-0 skeleton" aria-hidden />}
      <img
        src={src}
        alt={alt}
        loading="lazy"
        decoding="async"
        // sofifa's CDN 403s when a localhost/site referer is sent (hotlink
        // protection). Suppressing the referer header makes the photos load.
        referrerPolicy="no-referrer"
        onError={() => setFailed(true)}
        onLoad={() => setLoaded(true)}
        className={cn(
          'h-full w-full transition-opacity duration-500',
          fit === 'contain' ? 'object-contain' : 'object-cover',
          loaded ? 'opacity-100' : 'opacity-0',
          imgClassName,
        )}
      />
    </div>
  )
}

function ShieldGlyph() {
  return (
    <svg width="55%" height="55%" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
      <path d="M12 2 4 5v6c0 5 3.4 8.5 8 11 4.6-2.5 8-6 8-11V5l-8-3Z" strokeLinejoin="round" />
    </svg>
  )
}
