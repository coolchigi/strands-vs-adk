terraform {
  required_version = ">= 1.1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      # TODO: change this to "~> 6.66", run terraform init (observe the error),
      # run terraform init -upgrade, then restore it to "~> 6.0" and run
      # terraform init -upgrade one final time.
      version = "~> 6.66"
    }
  }

  backend "s3" {
    bucket         = "my-company-tf-state"
    key            = "myproject/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "my-company-tf-locks"
    encrypt        = true
  }
}
