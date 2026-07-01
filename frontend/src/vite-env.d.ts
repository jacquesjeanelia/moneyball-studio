/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL for the Moneyball API, e.g. "https://api.example.com". Empty = same-origin/proxy. */
  readonly VITE_API_BASE_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
