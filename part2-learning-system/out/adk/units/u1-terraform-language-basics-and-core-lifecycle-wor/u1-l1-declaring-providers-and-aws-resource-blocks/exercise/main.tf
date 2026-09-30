terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_requesting_account_id  = true

  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
  }
}

# TODO: Declare an aws_vpc resource named "main" with cidr_block = "10.0.0.0/16"

# TODO: Declare an aws_s3_bucket resource named "data" with bucket = "my-learning-bucket-2024"
