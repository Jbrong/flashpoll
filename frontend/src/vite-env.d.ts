/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** API origin. Empty (the default) means same-origin `/api`. */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
