import { vi } from 'vitest';

/**
 * Stub global fetch with a route table: { 'GET /api/polls/abc': response | fn(request) }.
 * A response is { status: <number>, body } or a plain body (status 200). Returns the mock so tests can
 * inspect calls; `requests` holds parsed { method, path, headers, body } for each call.
 */
export function mockApi(routes) {
  const requests = [];
  const fetchMock = vi.fn(async (url, init = {}) => {
    const method = init.method ?? 'GET';
    const path = new URL(url, 'http://localhost').pathname;
    const request = {
      method,
      path,
      headers: init.headers ?? {},
      body: init.body ? JSON.parse(init.body) : undefined,
    };
    requests.push(request);

    let handler = routes[`${method} ${path}`];
    if (handler === undefined) throw new Error(`Unmocked request: ${method} ${path}`);
    if (typeof handler === 'function') handler = handler(request);
    const { status = 200, body = null } =
      typeof handler?.status === 'number' ? handler : { body: handler };
    return new Response(status === 204 ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  });
  vi.stubGlobal('fetch', fetchMock);
  fetchMock.requests = requests;
  return fetchMock;
}

export const apiError = (status, code, message = code) => ({
  status,
  body: { error: { code, message } },
});
