# Flashpoll infrastructure

Terraform for everything in AWS. One stack (`./`) plus a one-time state bootstrap
(`./bootstrap`).

```
Route 53 ─▶ CloudFront ─┬─ /*      ─▶ S3 (private, Origin Access Control)
  (ACM cert,            │            + viewer-request function: SPA routing, www → apex
   security headers)    └─ /api/*  ─▶ API Gateway (HTTP API, throttled)
                                       ─▶ Lambda (FastAPI via Mangum, python3.13 arm64)
                                          ─▶ DynamoDB: polls + votes (on-demand, TTL)
```

| Module | What it creates |
|---|---|
| `modules/dynamodb` | `polls` and `votes` tables with TTL and the admin-token GSI |
| `modules/api` | Lambda, least-privilege IAM role, HTTP API, access logs, throttling |
| `modules/site` | S3 bucket, CloudFront distribution and function, ACM cert, DNS records, security headers |

### How requests reach the API safely

- CloudFront adds a secret `X-Origin-Verify` header to every `/api/*` request. The Lambda
  rejects requests without it, so the raw API Gateway URL is useless on its own.
- The API reads the voter's IP from `CloudFront-Viewer-Address`, which CloudFront sets and
  viewers can't forge. (`X-Forwarded-For` is ignored.)
- Only `Content-Type`, `X-Voter-Token`, `X-Admin-Token` and `CloudFront-Viewer-Address` are
  forwarded to the API. Access logs record no headers, so tokens never land in logs.

---

## First deploy (runbook)

### 0. Prerequisites

- AWS CLI v2, signed in to the target account with an admin-capable **non-root** identity
  (IAM Identity Center / SSO profile recommended): `aws sts get-caller-identity`
- Terraform ≥ 1.10, Python 3.13 + pipenv, Node 20+
- A **public Route 53 hosted zone for `flashpoll.dev` in the same account**. Check:

  ```bash
  aws route53 list-hosted-zones-by-name --dns-name flashpoll.dev --max-items 1
  ```

  If the domain was registered through Route 53 the zone already exists. If it was
  registered elsewhere, create the zone and point the registrar's name servers at it
  first — the certificate can't validate until DNS resolves through Route 53.

### 1. State bucket (once per account)

```bash
cd infrastructure/bootstrap
terraform init
terraform apply          # prints state_bucket = "flashpoll-tfstate-<account-id>"
```

This stack keeps its own small state file locally (git-ignored). Losing it is harmless;
the bucket is protected from `destroy`.

### 2. Initialise the main stack

```bash
cd infrastructure
cp backend.hcl.example backend.hcl         # put the bucket name from step 1 in it
cp terraform.tfvars.example terraform.tfvars   # optional; set budget_alert_email at least
terraform init -backend-config=backend.hcl
git add .terraform.lock.hcl                # commit the provider lock file
```

### 3. Build the API package

```bash
scripts/build_lambda.sh                    # from the repo root -> backend/dist/lambda.zip
```

### 4. Apply

```bash
cd infrastructure
terraform plan -out tfplan
terraform apply tfplan
```

Expect 5–15 minutes: the ACM certificate validates through DNS, then CloudFront deploys
globally.

### 5. Publish the frontend

```bash
scripts/deploy_frontend.sh                 # from the repo root
```

### 6. Smoke test

```bash
curl -s https://flashpoll.dev/api/health                     # {"status":"ok"}
curl -s "$(terraform -chdir=infrastructure output -raw api_endpoint)/api/health"
                                                             # 403 forbidden (no origin secret)
curl -sI https://www.flashpoll.dev/p/test | grep -i location # 301 -> https://flashpoll.dev/p/test
curl -sI https://flashpoll.dev/ | grep -i strict-transport   # HSTS header present
```

Then in a browser: create a poll, vote from a second browser, open the admin link, close
and delete it.

---

## Day-to-day

| Change | Command |
|---|---|
| Backend code | `scripts/build_lambda.sh && terraform -chdir=infrastructure apply` |
| Frontend code | `scripts/deploy_frontend.sh` |
| Infrastructure | `terraform -chdir=infrastructure plan`, then `apply` |
| API logs | `aws logs tail /aws/lambda/flashpoll-prod-api --follow` |

## Tearing down

```bash
cd infrastructure
terraform apply -var table_deletion_protection=false
terraform destroy
```

## Cost

At portfolio traffic this is close to free: Lambda, API Gateway, DynamoDB on-demand and
CloudFront all sit inside free tiers or cost cents. The fixed cost is the Route 53 hosted
zone ($0.50/month). Set `budget_alert_email` to get an email at 80% and 100% of
`monthly_budget_usd` (default $10).

## Not here yet

- **WAF** rate limits on votes and poll creation (Phase 3). Until then API Gateway
  throttling (`api_throttle_rate` / `api_throttle_burst`) caps total traffic.
- CloudWatch alarms and dashboards (Phase 3).
- CI/CD workflows (Phase 4).
- The origin secret lives in Terraform state and the Lambda's environment. Moving it to
  SSM Parameter Store / Secrets Manager with rotation is a reasonable Phase 3 item.
