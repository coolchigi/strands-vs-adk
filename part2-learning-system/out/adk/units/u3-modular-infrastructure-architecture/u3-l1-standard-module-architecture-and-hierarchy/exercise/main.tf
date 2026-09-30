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

# TODO: Call the child module 'vpc' using source "./modules/vpc"
# passing var.vpc_cidr and var.public_subnet_cidr.
module "vpc" {
  source             = "./modules/vpc"
  vpc_cidr           = ""
  public_subnet_cidr = ""
}

resource "aws_s3_bucket" "data" {
  bucket = "my-learning-bucket-2024"
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  subnet_id     = "" # TODO: Wire to module.vpc.public_subnet_id
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
