#!/usr/bin/env bash
# Build the frontend and publish it to the S3 bucket behind CloudFront.
# Reads the bucket and distribution from Terraform outputs.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BUCKET="$(terraform -chdir="$ROOT/infrastructure" output -raw site_bucket)"
DISTRIBUTION="$(terraform -chdir="$ROOT/infrastructure" output -raw cloudfront_distribution_id)"

cd "$ROOT/frontend"
npm ci
npm run build

# Fingerprinted assets never change: cache for a year. Everything else (index.html,
# icons) must revalidate so a deploy shows up immediately.
aws s3 sync dist/assets "s3://$BUCKET/assets" --delete \
  --cache-control "public, max-age=31536000, immutable"
aws s3 sync dist "s3://$BUCKET" --delete --exclude "assets/*" \
  --cache-control "no-cache"

aws cloudfront create-invalidation --distribution-id "$DISTRIBUTION" --paths "/*" \
  --query 'Invalidation.Id' --output text
echo "Deployed to s3://$BUCKET"
