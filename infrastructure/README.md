# Flashpoll infrastructure

Terraform for everything in AWS. One stack (`./`) plus a one-time state bootstrap
(`./bootstrap`).

```
Route 53 ─▶ CloudFront ─┬─ /*      ─▶ S3 (private, Origin Access Control)
  (ACM cert,            │            + viewer-request function: SPA routing, www → apex
   security headers)    └─ /api/*  ─▶ Lambda function URL
                                       (FastAPI via Mangum, python3.13 arm64)
                                          ─▶ DynamoDB: polls + votes (provisioned, TTL)
```

| Module | What it creates |
|---|---|
| `modules/dynamodb` | `polls` and `votes` tables with TTL and the admin-token GSI |
| `modules/api` | Lambda, least-privilege IAM role, function URL, log group |
| `modules/site` | S3 bucket, CloudFront distribution and function, ACM cert, DNS records, security headers |

### How requests reach the API safely

- CloudFront adds a secret `X-Origin-Verify` header to every `/api/*` request. The Lambda
  rejects requests without it, so the raw function URL is useless on its own.
- The API reads the voter's IP from `CloudFront-Viewer-Address`, which CloudFront sets and
  viewers can't forge. (`X-Forwarded-For` is ignored.)
- Only `Content-Type`, `X-Voter-Token`, `X-Admin-Token` and `CloudFront-Viewer-Address` are
  forwarded to the API, and the app never logs request headers, so tokens never land in logs.

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
cp terraform.tfvars.example terraform.tfvars   # set budget_alert_email (see "Cost")
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

If the function URL step fails with a `PublicPolicyException`, the account blocks public
Lambda resource policies; that setting has to allow the function URL's policy.

### 5. Publish the frontend

```bash
scripts/deploy_frontend.sh                 # from the repo root
```

### 6. Smoke test

```bash
curl -s https://flashpoll.dev/api/health                     # {"status":"ok"}
curl -s "$(terraform -chdir=infrastructure output -raw api_endpoint)api/health"
                                                             # 403 forbidden (no origin secret)
                                                             # (the function URL already ends in "/", hence no slash before api)
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

## Cost: staying in the free tier

The stack is built to run on AWS's **always-free** allowances, which never expire:

| Service | Always-free allowance | How the stack stays inside it |
|---|---|---|
| Lambda | 1M requests + 400,000 GB-seconds / month | One function, 512 MB, arm64 |
| Lambda function URL | No charge beyond Lambda | Used instead of API Gateway, whose free tier is 12 months / sign-up credits only |
| DynamoDB | 25 RCU + 25 WCU + 25 GB / region | **Provisioned** 21 RCU / 21 WCU total (on-demand is not covered) |
| CloudFront | 1 TB out + 10M requests + 2M function runs / month | Static assets cached at the edge |
| CloudWatch Logs | 5 GB ingestion / month | 7-day retention, no access logs |
| ACM, Budgets (first 2) | Free | |

What is **not** free:

- **Route 53 hosted zone: $0.50/month**, plus the yearly `.dev` domain renewal (~$12–15).
- **S3**: storage is a few hundred KB, so cents at most; it's only "free" during the
  12-month / credits period.
- Anything past the allowances above. Set `budget_alert_email`: it creates a budget that
  emails you on the **first cent** of actual spend, and when the month's forecast passes
  `monthly_budget_usd` ($1 by default).

Things to know:

- **The DynamoDB allowance is shared** by every provisioned table in the account and
  region. If the account has other tables, lower `dynamodb_capacity` so the total stays ≤ 25.
- **Provisioned capacity has a ceiling.** Roughly 2–5 votes/second sustained (burst capacity
  absorbs short spikes of a few hundred). Past that the API answers `503 busy` with
  `Retry-After` instead of failing. For a viral poll, switch
  `dynamodb_billing_mode = "PAY_PER_REQUEST"` (pay per request, cents per thousand votes).
- **Live results poll every 5 s**, so one open results page is ~720 requests/hour, against
  1M free Lambda requests a month.
- **New AWS accounts (created after 15 July 2025)** are on the credit-based Free plan, which
  ends after 6 months or when credits run out; the account then has to be upgraded to a paid
  plan to keep running. The always-free allowances above continue on the paid plan.
- **CloudFront flat-rate "Free" plan.** AWS also offers a $0/month CloudFront plan that
  bundles WAF, DDoS protection and Route 53 DNS for one distribution (1M requests, 100 GB).
  It's a console subscription, not Terraform, and its limits and feature restrictions should
  be checked in the console before switching — it may be the cheapest way to get WAF rate
  limiting (Phase 3).

## Not here yet

- **WAF** rate limits on votes and poll creation (Phase 3). Until then nothing caps request
  volume except DynamoDB's provisioned capacity; the zero-spend budget alert is the tripwire.
- CloudWatch alarms and dashboards (Phase 3).
- CI/CD workflows (Phase 4).
- The origin secret lives in Terraform state and the Lambda's environment. Moving it to
  SSM Parameter Store / Secrets Manager with rotation is a reasonable Phase 3 item.
