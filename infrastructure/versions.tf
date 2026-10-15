terraform {
  required_version = ">= 1.10" # S3 native state locking (use_lockfile)

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.68" # GSI key_schema blocks
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Partial configuration: bucket/region come from backend.hcl (see README.md).
  backend "s3" {
    key          = "flashpoll/terraform.tfstate"
    encrypt      = true
    use_lockfile = true
  }
}
