import { lazy, Suspense } from 'react'
import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence } from 'framer-motion'
import { NavBar } from '@/components/NavBar'
import { BrowsePage } from '@/pages/BrowsePage'
import { Spinner } from '@/components/states'

// Chart-heavy routes (recharts) are split out so the browse page stays lean.
const PlayerPage = lazy(() => import('@/pages/PlayerPage').then((m) => ({ default: m.PlayerPage })))
const SimilarPage = lazy(() => import('@/pages/SimilarPage').then((m) => ({ default: m.SimilarPage })))
const ComparePage = lazy(() => import('@/pages/ComparePage').then((m) => ({ default: m.ComparePage })))
const UmapPage = lazy(() => import('@/pages/UmapPage').then((m) => ({ default: m.UmapPage })))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage').then((m) => ({ default: m.NotFoundPage })))

export default function App() {
  const location = useLocation()
  return (
    <div className="min-h-screen flex flex-col">
      <NavBar />
      <main className="flex-1">
        <Suspense fallback={<div className="py-24"><Spinner label="Loading…" /></div>}>
          <AnimatePresence mode="wait">
            <Routes location={location} key={location.pathname}>
              <Route path="/" element={<BrowsePage />} />
              <Route path="/players/:id" element={<PlayerPage />} />
              <Route path="/players/:id/similar" element={<SimilarPage />} />
              <Route path="/compare/:idA/:idB" element={<ComparePage />} />
              <Route path="/map" element={<UmapPage />} />
              <Route path="*" element={<NotFoundPage />} />
            </Routes>
          </AnimatePresence>
        </Suspense>
      </main>
      <Footer />
    </div>
  )
}

function Footer() {
  return (
    <footer className="border-t border-ink-700 mt-20">
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-8 flex flex-col sm:flex-row items-center justify-between gap-4 text-sm text-chalk-faint">
        <div className="flex items-center gap-2">
          <span className="font-display font-bold text-chalk">MONEYBALL</span>
          <span className="text-signal-500 font-display font-bold">STUDIO</span>
        </div>
        <p>
          Performance data · Top 5 European leagues · 2024/2025 season ·{' '}
          <span className="text-chalk-dim">Similarity via pgvector cosine modelling</span>
        </p>
      </div>
    </footer>
  )
}
