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

resource "aws_s3_bucket" "storage" {
  # TODO: Set the bucket name to match the existing "my-learning-bucket-2024"
  bucket = ""
}

module "compute" {
  source = "./modules/compute"

  for_each      = var.instance_types
  subnet_id     = module.vpc.public_subnet_id
  instance_type = each.value
  environment   = each.key
}
