# ⚡ Flashpoll

> Create a poll in seconds. Share a link. Watch results live. It disappears when you're done.

Flashpoll is a dead-simple, no-account-required polling tool for anyone. No login walls, no setup friction, no data lingering forever. Create a poll, share it, and it auto-deletes when it expires.

**Live:** [flashpoll.dev](https://flashpoll.dev)

---

## 💡 What Makes It Different

| Feature | Flashpoll | Google Forms | Typeform |
|---|---|---|---|
| No account required | ✅ | ❌ | ❌ |
| Ephemeral / auto-deletes | ✅ | ❌ | ❌ |
| Real-time live results | ✅ | ❌ | ✅ (paid) |
| Super simple UI | ✅ | ⚠️ | ⚠️ |
| Free | ✅ | ✅ | ⚠️ |

Think of it as the **Snapchat of polls** — fast, frictionless, and ephemeral.

---

## 🗳️ How It Works

1. Visit [flashpoll.dev](https://flashpoll.dev)
2. Enter your question and up to 6 options
3. Choose your settings:
   - **Expiry** — 1 hour / 1 day / 1 week / custom (15 min–15 days)
   - **Vote control** — unlimited / one per browser / one per network (IP)
   - **Results visibility** — live / after voting / private
4. Click **Create** — you get two links instantly:
   - 🔗 **Share link** — `flashpoll.dev/p/abc123` — send to voters
   - 🔑 **Admin link** — `flashpoll.dev/admin#xyz789…` — keep private (close or delete the poll)

No account. No email. No friction.

The full product and API spec lives in [`docs/spec.md`](docs/spec.md).

---

## 🏛️ Architecture

Flashpoll runs on a fully serverless AWS stack — intentionally different from traditional containerized architectures to demonstrate range.

```
User → Route 53 → CloudFront → S3 (React frontend)
                      ↓
              API Gateway (REST + WebSocket)
                      ↓
                   Lambda
                      ↓
                  DynamoDB (TTL auto-deletes expired polls)
```

### Infrastructure

| Service | Purpose |
|---|---|
| Route 53 | Domain + DNS for flashpoll.dev |
| S3 + CloudFront | Static React frontend, global CDN |
| API Gateway (REST) | Poll CRUD — create, read, vote |
| API Gateway (WebSocket) | Real-time results push to connected clients |
| Lambda | Serverless backend functions (Python) |
| DynamoDB | Polls, votes, admin tokens — TTL for auto-expiry |
| WAF | Rate limiting on vote endpoint — prevent stuffing |
| CloudWatch | Monitoring, alarms, anomaly detection |
| ACM | SSL/TLS — HTTPS enforced everywhere |

### Why Serverless + DynamoDB?

**DynamoDB TTL** is the elegant solution to ephemeral polls — when a poll expires, DynamoDB deletes the record automatically. No cron jobs, no cleanup scripts, no stale data.

**WebSocket API via API Gateway** pushes vote updates to all connected clients in real time. When someone votes, everyone watching the results page sees it instantly.

**Lambda over ECS/Fargate** — for a stateless, event-driven workload like this, serverless is the right fit. No containers to manage, no idle compute costs.

---

## 🔒 Security Design

- **WAF rate limiting** on the vote endpoint — configurable per poll, enforces one-per-IP when selected
- **DynamoDB TTL** handles data lifecycle automatically — no lingering PII after expiry
- **Admin tokens** are 192-bit random secrets; only their SHA-256 hash is stored. The token travels in the URL fragment (never sent to the server, so never in access logs) and as a `Bearer` header to the API
- **Server-enforced rules** — vote control and results visibility are checked by the API, not just hidden in the UI
- **No raw IPs stored** — vote-control markers are per-poll hashes
- **Lambda execution roles** scoped to minimum required permissions — no wildcards
- **No user accounts in v1** — minimal attack surface by design
- **HTTPS enforced** via CloudFront + ACM — no plain HTTP

---

## 📁 Project Structure

```
flashpoll/
├── frontend/              # React + TypeScript + Vite single-page app
│   ├── src/pages/         # Create, vote/results, admin pages
│   ├── src/components/    # Shared UI (results bars, copy fields, layout)
│   └── src/lib/           # API client, voter token, helpers
├── backend/               # Python API (FastAPI; runs on Lambda via Mangum)
│   ├── flashpoll/         # App package: routes, service rules, DynamoDB store
│   ├── tests/             # pytest suite against mocked DynamoDB (moto)
│   ├── scripts/           # Local table bootstrap
│   └── lambda_handler.py  # AWS Lambda entry point
├── infrastructure/        # Terraform — all AWS resources
├── docs/spec.md           # Product, API and data model spec
└── docker-compose.yml     # DynamoDB Local
```

---

## 🚀 Running Locally

### Prerequisites
- Node.js 20+
- Python 3.13 + [pipenv](https://pipenv.pypa.io/)
- Docker (for DynamoDB Local)

### 1. Database

```bash
docker compose up -d                 # DynamoDB Local on :8000
```

### 2. Backend

```bash
cd backend
cp .env.example .env
pipenv install --dev
pipenv run bootstrap                 # create the tables in DynamoDB Local
pipenv run dev                       # API on http://localhost:8080 (docs at /api/docs)
```

### 3. Frontend

```bash
cd frontend
npm ci
npm run dev                          # http://localhost:5173, proxies /api to :8080
```

### Tests

```bash
cd backend  && pipenv run test && pipenv run lint
cd frontend && npm run typecheck && npm test
```

Backend tests use [moto](https://github.com/getmoto/moto) to mock DynamoDB, so they don't need Docker.

---

## ⚙️ Deployment

Infrastructure managed with Terraform. Lambda functions deployed via GitHub Actions on push to `main`.

```bash
cd infrastructure/
terraform init
terraform plan
terraform apply
```

GitHub Actions workflows:
- `frontend-deploy.yml` — Build React → upload to S3 → invalidate CloudFront cache
- `backend-deploy.yml` — Package Python → deploy Lambda functions via AWS CLI
- `terraform-plan.yml` — Run `terraform plan` on all PRs

---

## 📊 Data Model

Two DynamoDB tables, both with TTL on `ttl`:

- **`flashpoll-polls`** — one item per poll: question, options, settings, live vote `counts`, `expires_at`, and `ttl` (= expiry + 24h grace). GSI on `admin_token_hash`.
- **`flashpoll-votes`** — one marker per voter (hashed browser token or IP) to enforce vote control.

Votes are counted atomically with a DynamoDB transaction, so reading results is a single `GetItem`. Details in [`docs/spec.md`](docs/spec.md#3-data-model-dynamodb).

---

## 🗺️ Roadmap

- [x] Concept defined
- [x] Domain registered (flashpoll.dev)
- [x] Architecture designed
- [ ] Phase 1 — Core (poll CRUD, DynamoDB TTL, shareable links) — code + tests done, deploy pending
- [ ] Phase 2 — Real-time (WebSocket live results)
- [ ] Phase 3 — Security hardening (WAF, CloudWatch alarms)
- [ ] Phase 4 — Terraform IaC, architecture writeup, portfolio polish

---

## 👤 About

Built by Jordan Brong — DevOps Engineer pursuing a Cloud Security Architect path.

- Certs: AWS Cloud Practitioner ✅ | SAA-C03 (in progress) | SCS-C02 (queued)
- [LinkedIn](https://linkedin.com/in/[your-handle])
- [Wildmark](https://wildmark.dev) — my other portfolio project

---

## 📄 License

MIT — see [LICENSE](LICENSE)