// A random per-browser ID used for "one vote per browser" and "results after voting".
// It is a courtesy limit, not a security control (docs/spec.md, 1.3).
const STORAGE_KEY = 'flashpoll.voterToken';
let memoryToken = null;

function newToken() {
  return crypto.randomUUID();
}

export function getVoterToken() {
  try {
    let token = localStorage.getItem(STORAGE_KEY);
    if (!token) {
      token = newToken();
      localStorage.setItem(STORAGE_KEY, token);
    }
    return token;
  } catch {
    // Storage blocked (private mode, disabled cookies): fall back to this page load only.
    memoryToken ??= newToken();
    return memoryToken;
  }
}
