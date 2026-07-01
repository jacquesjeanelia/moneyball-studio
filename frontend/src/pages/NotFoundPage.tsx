import { Link } from 'react-router-dom'
import { PageTransition } from '@/components/PageTransition'

export function NotFoundPage() {
  return (
    <PageTransition>
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 py-32 flex flex-col items-center text-center">
        <div className="font-display font-extrabold text-8xl sm:text-9xl text-ink-700 leading-none select-none">404</div>
        <h1 className="font-display font-bold text-2xl text-chalk mt-2">Off the pitch</h1>
        <p className="text-chalk-dim mt-2 max-w-sm">
          That page doesn't exist. Let's get you back to the scouting board.
        </p>
        <Link
          to="/"
          className="mt-6 rounded-lg accent-bar px-5 py-2.5 text-sm font-bold text-white shadow-glow hover:brightness-110 transition"
        >
          Back to search
        </Link>
      </div>
    </PageTransition>
  )
}
