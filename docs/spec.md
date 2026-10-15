# Flashpoll — Product & Technical Spec

Status: **draft v1** · Owner: Jordan Brong · Last updated: 2026-10-15

This is the source of truth for what Flashpoll does. The README is the pitch; this file is
the contract. Anything marked **Decision** was chosen while drafting and is open to change —
see [Open decisions](#open-decisions) for the ones most worth a second look.

---

## 1. Product

Flashpoll lets anyone create a poll without an account, share a link, watch results, and
have everything deleted automatically when the poll is done.

### 1.1 Pages

| Path | Page | Who |
|---|---|---|
| `/` | Create poll | Anyone |
| `/p/{pollId}` | Vote + results | Anyone with the share link |
| `/admin#{adminToken}` | Manage poll | Whoever holds the admin link |
| anything else | Not found | — |

### 1.2 Creating a poll

Inputs:

| Field | Rule |
|---|---|
| Question | 1–200 characters after trimming |
| Options | 2–6 options, each 1–100 characters after trimming, unique (case-insensitive). Original casing is kept. |
| Expiry | Presets: 1 hour, 1 day, 1 week. Custom: any duration from 15 minutes to 15 days. Sent to the API as whole minutes (15–21600). |
| Vote control | `open` · `one_per_browser` · `one_per_ip` (default `one_per_browser`) |
| Results visibility | `live` · `after_voting` · `private` (default `live`) |

On success the creator sees two links:

- **Share link** — `https://flashpoll.dev/p/{pollId}`
- **Admin link** — `https://flashpoll.dev/admin#{adminToken}`

The admin token sits in the URL *fragment* (after `#`). Browsers never send the fragment to
the server, so it stays out of CloudFront/S3 access logs and `Referer` headers.

The admin link is shown **once**. The server stores only a hash of the admin token, so a
lost admin link cannot be recovered. The UI says so and offers copy buttons.

### 1.3 Voting

- A voter picks exactly one option and submits. Votes cannot be changed.
- Vote control:
  - `open` — no restriction. Anyone can vote any number of times.
  - `one_per_browser` — one vote per browser, tracked by a random *voter token* the frontend
    keeps in `localStorage`. Clearing storage or using another browser allows another vote.
    This is a courtesy limit, not a security control, and the UI wording should not imply
    otherwise.
  - `one_per_ip` — one vote per client IP address. Stronger, but blocks people sharing a
    network (offices, dorms, mobile carriers).
- After a successful vote the page shows results if the voter is allowed to see them
  (see 1.4), otherwise a "Thanks for voting" message.
- Reloading the page remembers that this browser already voted.

### 1.4 Results visibility

| Setting | Who sees results while open | Who sees results after close |
|---|---|---|
| `live` | Everyone | Everyone |
| `after_voting` | Browsers that have voted on this poll | Everyone |
| `private` | Admin only | Admin only |

Enforced by the **server**, not just hidden in the UI.

Results show, per option: count and percentage, plus total votes. While the poll is open
and results are visible, the page refreshes them every 5 seconds (Phase 1). Phase 2 replaces
polling with WebSocket push.

### 1.5 Poll lifecycle

```
created ──(expires_at reached, or admin closes)──▶ closed ──(24h grace)──▶ deleted
   │                                                                          ▲
   └──────────────────────(admin deletes)─────────────────────────────────────┘
```

- **Open**: accepts votes until `expires_at`.
- **Closed**: no more votes. Results stay viewable (per 1.4) for a **24-hour grace period**
  so the creator and voters can see the final tally.
- **Deleted**: the poll and all its vote records are gone. DynamoDB TTL does this at
  `expires_at + 24h`. TTL deletion can lag by up to ~48h, so the API also treats any record
  past its `ttl` as not found.
- Closing early sets `expires_at` to now; the deletion time does not move.

### 1.6 Admin page

With the admin link, the creator can:

- See the poll, its status, time remaining, and full results (regardless of visibility setting).
- **Close voting now.**
- **Delete the poll now** (with a confirmation step). This is immediate and permanent.

### 1.7 Out of scope for v1

Accounts, editing a poll after creation, multi-select / ranked voting, images, comments,
embedding, analytics, recovering a lost admin link.

---

## 2. API

Base path `/api`. JSON in and out. In production the frontend and API share an origin
(CloudFront routes `/api/*` to API Gateway), so CORS is only needed for local dev.

### 2.1 Errors

Every non-2xx response has this body:

```json
{ "error": { "code": "poll_not_found", "message": "Poll not found" } }
```

| HTTP | `code` | When |
|---|---|---|
| 401 | `unauthorized` | Missing or invalid admin token |
| 403 | `results_hidden` | Results not visible to this caller (1.4) |
| 403 | `forbidden` | Request didn't come through CloudFront (missing origin secret, 4.2) |
| 404 | `poll_not_found` | Unknown, deleted, or past-TTL poll |
| 404 | `not_found` | Unknown route |
| 409 | `poll_closed` | Vote on a closed poll |
| 409 | `already_voted` | Vote control rejected a repeat vote |
| 422 | `invalid_request` | Body/params fail validation; `error.fields` lists problems |
| 503 | `busy` | DynamoDB capacity exhausted (free-tier provisioned throughput); `Retry-After` is set |
| 500 | `internal_error` | Anything else |

### 2.2 Headers

| Header | Used by | Purpose |
|---|---|---|
| `X-Voter-Token` | poll, vote, results | Identifies this browser for `one_per_browser` and `after_voting`. 16–64 chars of `[A-Za-z0-9_-]`. |
| `X-Admin-Token: {adminToken}` | admin endpoints | Admin auth. Kept out of the URL so it doesn't land in access logs. A custom header rather than `Authorization` so CloudFront can forward it with a plain allowlist. |

### 2.3 Endpoints

#### `POST /api/polls` → `201`

```json
// request
{
  "question": "What should we have for lunch?",
  "options": ["Pizza", "Tacos", "Salad"],
  "expires_in_minutes": 1440,
  "vote_control": "one_per_browser",
  "results_visibility": "after_voting"
}
// response
{
  "poll_id": "Xk3_9aQz",
  "admin_token": "q0V…32 chars…",
  "share_url": "https://flashpoll.dev/p/Xk3_9aQz",
  "admin_url": "https://flashpoll.dev/admin#q0V…",
  "expires_at": "2026-10-16T18:00:00Z"
}
```

This is the only response that ever contains the admin token.

#### `GET /api/polls/{pollId}` → `200`

Public view of a poll. Never includes admin data.

```json
{
  "poll_id": "Xk3_9aQz",
  "question": "What should we have for lunch?",
  "options": ["Pizza", "Tacos", "Salad"],
  "vote_control": "one_per_browser",
  "results_visibility": "after_voting",
  "created_at": "2026-10-15T18:00:00Z",
  "expires_at": "2026-10-16T18:00:00Z",
  "status": "open",          // "open" | "closed"
  "has_voted": false,        // for the X-Voter-Token sent; false if none
  "results_available": false // whether GET /results would succeed for this caller
}
```

#### `POST /api/polls/{pollId}/votes` → `200`

```json
// request (X-Voter-Token header required for one_per_browser)
{ "option_index": 1 }
// response — results is null when the caller may not see them
{ "results": { "total_votes": 12, "counts": [5, 6, 1] } }
```

#### `GET /api/polls/{pollId}/results` → `200`

```json
{ "status": "open", "total_votes": 12, "counts": [5, 6, 1] }
```

`counts[i]` is the vote count for `options[i]`. Percentages are computed by the client.

#### `GET /api/admin/poll` → `200`

Admin auth (`X-Admin-Token`). Returns the public poll view plus `results` and `deletes_at`.

#### `POST /api/admin/poll/close` → `200`

Admin auth (`X-Admin-Token`). Closes voting now. Idempotent. Returns the same body as `GET /api/admin/poll`.

#### `DELETE /api/admin/poll` → `204`

Admin auth (`X-Admin-Token`). Deletes the poll and all its vote records.

#### `GET /api/health` → `200`

`{ "status": "ok" }`. For load balancer / smoke checks.

---

## 3. Data model (DynamoDB)

Two tables, both with TTL on attribute `ttl`. Provisioned capacity in AWS (free tier), on-demand locally.

### 3.1 `polls`

| Attribute | Type | Notes |
|---|---|---|
| `poll_id` (PK) | S | 8-char URL-safe random ID (48 bits). Created with a conditional put; retried on collision. |
| `admin_token_hash` | S | SHA-256 hex of the admin token. GSI `admin_token_hash-index`, keys-only projection (vote updates never touch the index). |
| `question` | S | |
| `options` | L of S | Original casing |
| `vote_control` | S | |
| `results_visibility` | S | |
| `counts` | M | `{"0": n, "1": n, …}` — incremented atomically per vote |
| `total_votes` | N | |
| `created_at` | N | Unix seconds |
| `expires_at` | N | Unix seconds. Voting closes here. |
| `ttl` | N | `expires_at + 86400` (original expiry; unchanged on early close) |

Admin token: 32-char URL-safe random (192 bits). Only its hash is stored.

### 3.2 `votes`

One item per *voter marker* — what's needed to enforce vote control and `after_voting`. The
tally itself lives on the poll item, so reading results is a single `GetItem`, not a scan of
all votes.

| Attribute | Type | Notes |
|---|---|---|
| `poll_id` (PK) | S | |
| `voter_key` (SK) | S | `vt#{hash}` (voter token) or `ip#{hash}` (client IP) |
| `created_at` | N | |
| `ttl` | N | Same as the poll's |

`hash` = SHA-256 of `{poll_id}:{value}`. Raw IPs and voter tokens are never stored.

### 3.3 Vote write path

A vote is one `TransactWriteItems`:

1. `Update` the poll: `ADD counts.#i :1, total_votes :1`, condition
   `attribute_exists(poll_id) AND expires_at > :now`.
2. `Put` an `ip#` marker with `attribute_not_exists(voter_key)` — only for `one_per_ip`.
3. `Put` a `vt#` marker when a voter token is sent — with `attribute_not_exists(voter_key)`
   only for `one_per_browser`, unconditional otherwise (it records "has voted" for
   `after_voting`).

All-or-nothing: a rejected repeat vote never increments the count.

---

## 4. Architecture

### 4.1 Runtime

- **Backend**: one FastAPI app (`backend/flashpoll`). Locally it runs under uvicorn; in AWS
  it runs as a single Lambda behind a Lambda function URL via the Mangum adapter
  (`backend/lambda_handler.py`). **Decision**: one "monolith" Lambda rather than one Lambda
  per route — simpler to deploy, test and run locally, and cold starts stay small at this size.
  **Decision**: a function URL rather than API Gateway, to stay in the always-free tier.
- **Frontend**: React + Vite, static build served from S3 via CloudFront.
- **Data**: DynamoDB, as above.

### 4.2 Client IP and origin protection

`one_per_ip` needs the real client IP. Behind CloudFront + API Gateway the socket peer is
not the client, and `X-Forwarded-For` can be partly forged by the caller. Instead:

- CloudFront forwards `CloudFront-Viewer-Address` (`ip:port`), which it sets itself. The API
  reads the IP from the header named by `CLIENT_IP_HEADER`; locally that is unset and the
  socket peer is used.
- CloudFront adds a secret `X-Origin-Verify` header to every API request. When
  `ORIGIN_VERIFY_SECRET` is set, the API rejects requests without it (403 `forbidden`), so
  nobody can call API Gateway directly and forge the viewer header.

### 4.3 Configuration (backend env)

| Var | Default | Purpose |
|---|---|---|
| `APP_URL` | `http://localhost:5173` | Base for `share_url` / `admin_url` |
| `AWS_REGION` | `us-east-1` | |
| `DYNAMODB_URL` | unset | Endpoint override for DynamoDB Local |
| `POLLS_TABLE` | `flashpoll-polls` | |
| `VOTES_TABLE` | `flashpoll-votes` | |
| `CORS_ORIGINS` | `http://localhost:5173` | Comma-separated; empty disables CORS |
| `CLIENT_IP_HEADER` | unset | Header holding the client IP (`CloudFront-Viewer-Address` in AWS) |
| `ORIGIN_VERIFY_SECRET` | unset | Required `X-Origin-Verify` value (set by Terraform in AWS) |

### 4.4 AWS deployment

Terraform in `infrastructure/` (runbook in `infrastructure/README.md`):

- **CloudFront** serves the S3 frontend (private bucket, Origin Access Control) and routes
  `/api/*` to API Gateway with caching disabled. A CloudFront Function rewrites app routes
  to `index.html` and redirects `www` to the apex. A response-headers policy sets HSTS, CSP,
  `X-Frame-Options: DENY`, `nosniff` and `Referrer-Policy`.
- **Lambda function URL** → one **Lambda** (python3.13, arm64) running the FastAPI app via
  Mangum. The URL is public but useless without CloudFront's origin secret.
- **DynamoDB** tables as in section 3, **provisioned** capacity sized inside the always-free
  tier (21 RCU / 21 WCU total), TTL enabled, deletion protection on.
- **Cost target: the AWS always-free tier.** The only fixed cost is the Route 53 hosted zone.
  A budget alert fires on the first cent of spend.
- Terraform state in a versioned, encrypted S3 bucket with native locking.

---

## 5. Phases

| Phase | Scope | Done when |
|---|---|---|
| **1 — Core** | Everything in sections 1–3 except WebSocket push. Local dev with DynamoDB Local. | Backend and frontend tests pass; full flow works locally (create → vote → results → admin close/delete). |
| **2 — Real-time** | Push new counts to open results pages instead of 5-second polling. **Open question:** API Gateway WebSockets aren't in the always-free tier, so this needs a free-tier-compatible design (or a decision to accept a small cost). | Two browsers on one poll see each other's votes in under 1s. |
| **3 — Security hardening** | WAF rate limits (votes per IP, creates per IP), CloudWatch alarms and dashboards, origin secret in Secrets Manager. (Security headers and origin protection already shipped with the Phase 1 infra.) | Rate limits verified; alarms fire on test traffic. |
| **4 — IaC & polish** | All AWS resources in Terraform; GitHub Actions for test, plan, deploy; architecture diagram and write-up. | Clean `terraform apply` from scratch; CI deploys on merge to `master`. |

Phase 4's Terraform work is being pulled forward to deploy Phase 1.

---

## Open decisions

These were chosen while drafting; change any of them before they harden.

1. **24-hour grace period** after close before deletion. Alternative: delete at expiry
   (more "ephemeral", but the creator never sees the final tally of an expired poll).
2. **`private` results stay admin-only after close.** Alternative: reveal to everyone at close.
3. **Votes are final** — no changing your vote.
4. **Admin link is unrecoverable** (only a hash is stored).
5. **Default vote control `one_per_browser`, default visibility `live`.**
6. **Single Lambda** running the whole FastAPI app, exposed by a function URL rather than
   API Gateway (4.1) — chosen for the always-free tier.
9. **Free-tier first.** Provisioned DynamoDB (caps throughput at a few votes/second
   sustained) instead of on-demand; real-time push (Phase 2) must fit the free tier too.
7. **URL shapes** `/p/{id}` (as in the README) and `/admin#{token}` (fragment instead of the
   README's `/admin/{token}`, to keep the token out of server logs).
8. **Python 3.13** (newest Lambda runtime) instead of 3.10.
