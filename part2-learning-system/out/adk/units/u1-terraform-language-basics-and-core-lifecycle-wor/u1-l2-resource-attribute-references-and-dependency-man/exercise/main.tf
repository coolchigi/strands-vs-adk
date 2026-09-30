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

resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_s3_bucket" "data" {
  bucket = "my-learning-bucket-2024"
}

resource "aws_internet_gateway" "gw" {
  # TODO: Reference the ID of aws_vpc.main
  vpc_id = ""
}

resource "aws_subnet" "public" {
  cidr_block = "10.0.1.0/24"
  # TODO: Reference the ID of aws_vpc.main
  vpc_id     = ""
}

resource "aws_route_table" "public" {
  # TODO: Reference the ID of aws_vpc.main
  vpc_id     = ""
  depends_on = [aws_internet_gateway.gw]
}
