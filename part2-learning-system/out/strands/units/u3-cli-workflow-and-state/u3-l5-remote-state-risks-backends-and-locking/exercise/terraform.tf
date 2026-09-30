terraform {
  required_version = ">= 1.1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # TODO: add a backend "s3" block here with:
  #   bucket         = "my-company-tf-state"
  #   key            = "myproject/dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "my-company-tf-locks"
  #   encrypt        = true
}
