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
  # TODO: Pass var.vpc_cidr to vpc_cidr
  vpc_cidr           = "172.16.0.0/16"
  # TODO: Pass var.public_subnet_cidr to public_subnet_cidr
  public_subnet_cidr = "172.16.1.0/24"
}

resource "aws_s3_bucket" "data" {
  bucket = "my-learning-bucket-2024"
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  # TODO: Reference the public subnet ID from module.vpc
  subnet_id     = ""
  instance_type = lookup(var.instance_types, var.environment, "t3.nano")
  user_data     = templatefile("${path.module}/userdata.sh.tftpl", {
    server_name = "${var.environment}-server"
  })

  tags = merge(
    {
      Name        = "${var.environment}-web"
      Environment = var.environment
    },
    var.extra_tags
  )
}
