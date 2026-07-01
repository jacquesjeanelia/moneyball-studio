import { Link, useLocation } from 'react-router-dom'

export function NavBar() {
  const location = useLocation()
  const onHome = location.pathname === '/'

  return (
    <header className="sticky top-0 z-50 glass border-b border-ink-700">
      <div className="max-w-[1400px] mx-auto px-5 sm:px-8 h-16 flex items-center justify-between gap-6">
        <Link to="/" className="group flex items-center gap-2.5 shrink-0">
          <span className="relative flex h-8 w-2.5">
            <span className="accent-bar absolute inset-0 rounded-sm transition-transform duration-300 group-hover:scale-y-110" />
          </span>
          <span className="font-display font-extrabold text-xl tracking-tight leading-none">
            <span className="text-chalk">MONEYBALL</span>{' '}
            <span className="text-signal-500">STUDIO</span>
          </span>
        </Link>

        <nav className="flex items-center gap-1 text-sm font-semibold">
          <NavLink to="/" active={onHome}>
            Search
          </NavLink>
        </nav>
      </div>
    </header>
  )
}

function NavLink({ to, active, children }: { to: string; active: boolean; children: React.ReactNode }) {
  return (
    <Link
      to={to}
      aria-current={active ? 'page' : undefined}
      className={
        'relative px-3 py-2 rounded-lg transition-colors ' +
        (active ? 'text-chalk' : 'text-chalk-dim hover:text-chalk hover:bg-ink-700/60')
      }
    >
      {children}
      {active && <span className="absolute left-3 right-3 -bottom-px h-0.5 accent-bar rounded-full" />}
    </Link>
  )
}
