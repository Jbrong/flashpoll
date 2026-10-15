import { useEffect, useRef } from 'react';

/** Call `callback` every `intervalMs` while `enabled` and the tab is visible. */
export function usePolling(callback, intervalMs, enabled) {
  const saved = useRef(callback);
  useEffect(() => {
    saved.current = callback;
  }, [callback]);

  useEffect(() => {
    if (!enabled) return undefined;
    const id = setInterval(() => {
      if (document.visibilityState !== 'hidden') saved.current();
    }, intervalMs);
    return () => clearInterval(id);
  }, [intervalMs, enabled]);
}
