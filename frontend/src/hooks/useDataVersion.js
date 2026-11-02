import { useCallback, useEffect, useState } from 'react';

const POLL_FALLBACK_MS = 30000;

/**
 * Follows the backend data version.
 *
 * The backend refreshes its event cache every `reload_interval` minutes and pushes
 * `{version, last_refresh, next_refresh, interval}` over SSE. Views add `version`
 * to their fetch dependencies, so every open view reloads on the same backend refresh.
 * If the stream drops, `/api/version` is polled until it reconnects.
 */
export default function useDataVersion() {
  const [state, setState] = useState({ version: null, nextRefresh: null, interval: 0 });

  const apply = useCallback((data) => {
    setState({ version: data.version, nextRefresh: data.next_refresh, interval: data.interval });
  }, []);

  useEffect(() => {
    let pollTimer = null;
    const poll = () => fetch('/api/version').then(r => r.json()).then(apply).catch(() => {});
    const stopPolling = () => { clearInterval(pollTimer); pollTimer = null; };

    const source = new EventSource('/api/events/stream');
    source.onmessage = (e) => {
      stopPolling();
      try { apply(JSON.parse(e.data)); } catch { /* ignore malformed frame */ }
    };
    source.onerror = () => {
      // EventSource retries on its own; poll meanwhile so the UI keeps up.
      if (!pollTimer) {
        poll();
        pollTimer = setInterval(poll, POLL_FALLBACK_MS);
      }
    };

    return () => {
      source.close();
      stopPolling();
    };
  }, [apply]);

  const refreshNow = useCallback(async () => {
    const res = await fetch('/api/refresh', { method: 'POST' });
    apply(await res.json());
  }, [apply]);

  return { ...state, refreshNow };
}
