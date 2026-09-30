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

module "vpc" {
  source             = "./modules/vpc"
  vpc_cidr           = var.vpc_cidr
  public_subnet_cidr = var.public_subnet_cidr
}

resource "aws_s3_bucket" "data" {
  bucket = "my-learning-bucket-2024"
}

module "compute" {
  source = "./modules/compute"

  # TODO: Deploy instances for each environment in var.instance_types using for_each
  for_each = {}

  # TODO: Pass the public subnet ID from module.vpc
  subnet_id = ""

  # TODO: Pass instance type from each.value and environment from each.key
  instance_type = ""
  environment   = ""
}
