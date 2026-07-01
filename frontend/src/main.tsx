import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter } from 'react-router-dom'
import { MotionConfig } from 'framer-motion'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {/* reducedMotion="user" makes every framer-motion animation respect
            prefers-reduced-motion (transforms/layout become instant; opacity
            kept). Pairs with the CSS reduced-motion block for full coverage. */}
        <MotionConfig reducedMotion="user">
          <App />
        </MotionConfig>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
