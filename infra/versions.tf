terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  # Existing shared state bucket; the default workspace stores state at this exact key.
  # use_lockfile = native S3 state locking, no DynamoDB lock table needed.
  backend "s3" {
    bucket       = "marx-aws-tfstates"
    key          = "dig-out"
    region       = "eu-central-1"
    use_lockfile = true
    encrypt      = true
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      project    = var.project
      env        = var.env
      managed-by = "terraform"
    }
  }
}

# CloudFront requires ACM certificates in us-east-1.
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"

  default_tags {
    tags = {
      project    = var.project
      env        = var.env
      managed-by = "terraform"
    }
  }
}

data "aws_caller_identity" "current" {}

locals {
  prefix     = "${var.project}-${var.env}"
  account_id = data.aws_caller_identity.current.account_id
}
