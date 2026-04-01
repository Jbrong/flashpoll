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
   - **Vote control** — open / one per browser / one per IP
   - **Results visibility** — live / after voting / private
4. Click **Create** — you get two links instantly:
   - 🔗 **Share link** — `flashpoll.dev/p/abc123` — send to voters
   - 🔑 **Admin link** — `flashpoll.dev/admin/xyz789` — keep private

No account. No email. No friction.

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
- **Admin tokens** are UUID v4 secrets stored in DynamoDB — no auth system needed for v1
- **Lambda execution roles** scoped to minimum required permissions — no wildcards
- **No user accounts in v1** — minimal attack surface by design
- **HTTPS enforced** via CloudFront + ACM — no plain HTTP

---

## 📁 Project Structure

```
flashpoll/
├── frontend/          # React app
├── backend/           # Python Lambda functions
│   ├── polls/         # Create, read, delete poll handlers
│   ├── votes/         # Vote handler
│   ├── websocket/     # WebSocket connect/disconnect/broadcast
│   └── shared/        # Shared utilities, DynamoDB client
├── infrastructure/    # Terraform — all AWS resources
│   └── modules/       # api_gateway, lambda, dynamodb, cloudfront, waf
├── docs/
│   ├── architecture/  # System diagrams
│   └── writeup.md     # Portfolio case study
├── .github/workflows/ # CI/CD — deploy frontend + Lambda functions
├── .env.example
└── README.md
```

---

## 🚀 Running Locally

### Prerequisites
- Node.js 18+
- Python 3.11+
- AWS SAM CLI or Docker (for local Lambda)
- AWS CLI (configured)

### Setup

```bash
git clone https://github.com/Jbrong/flashpoll.git
cd flashpoll
cp .env.example .env        # Fill in local dev values
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev                 # Runs at http://localhost:3000
```

**Backend (Lambda locally via SAM):**
```bash
cd backend
sam local start-api         # Runs API at http://localhost:3001
```

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

**Poll record (DynamoDB):**
```json
{
  "pollId": "abc123",
  "adminToken": "xyz789-uuid-v4",
  "question": "What should we have for lunch?",
  "options": ["Pizza", "Tacos", "Salad"],
  "voteControl": "one_per_browser",
  "resultsVisibility": "after_voting",
  "expiresAt": 1234567890,
  "ttl": 1234567890
}
```

`ttl` = DynamoDB TTL attribute — record auto-deletes at expiry. No cleanup needed.

---

## 🗺️ Roadmap

- [x] Concept defined
- [x] Domain registered (flashpoll.dev)
- [x] Architecture designed
- [ ] Phase 1 — Core (poll CRUD, DynamoDB TTL, shareable links)
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