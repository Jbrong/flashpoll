import { type Mock, vi } from 'vitest';

export interface RecordedRequest {
  method: string;
  path: string;
  headers: Record<string, string>;
  // Parsed JSON body. Typed loosely so tests can assert on fields directly.
  body: any;
}

interface MockResponse {
  status: number;
  body?: unknown;
}

/** A canned response: { status: <number>, body } or a plain body (status 200). */
type Handler = MockResponse | object | null | ((request: RecordedRequest) => MockResponse | object | null);

export type ApiMock = Mock<typeof fetch> & { requests: RecordedRequest[] };

const isResponse = (value: unknown): value is MockResponse =>
  typeof (value as MockResponse | null)?.status === 'number';

/**
 * Stub global fetch with a route table: { 'GET /api/polls/abc': handler }.
 * `requests` on the returned mock records every call in order.
 */
export function mockApi(routes: Record<string, Handler>): ApiMock {
  const requests: RecordedRequest[] = [];
  const fetchMock = vi.fn(async (url: RequestInfo | URL, init: RequestInit = {}) => {
    const method = init.method ?? 'GET';
    const path = new URL(String(url), 'http://localhost').pathname;
    const request: RecordedRequest = {
      method,
      path,
      headers: (init.headers ?? {}) as Record<string, string>,
      body: typeof init.body === 'string' ? JSON.parse(init.body) : undefined,
    };
    requests.push(request);

    const key = `${method} ${path}`;
    if (!(key in routes)) throw new Error(`Unmocked request: ${key}`);
    const route = routes[key];
    const handled = typeof route === 'function' ? route(request) : route;
    const { status, body = null } = isResponse(handled) ? handled : { status: 200, body: handled };
    return new Response(status === 204 ? null : JSON.stringify(body), {
      status,
      headers: { 'Content-Type': 'application/json' },
    });
  }) as ApiMock;
  fetchMock.requests = requests;
  vi.stubGlobal('fetch', fetchMock);
  return fetchMock;
}

export const apiError = (status: number, code: string, message: string = code): MockResponse => ({
  status,
  body: { error: { code, message } },
});
