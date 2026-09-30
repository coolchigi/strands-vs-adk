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
  cidr_block = var.vpc_cidr
}

resource "aws_s3_bucket" "data" {
  bucket = "my-learning-bucket-2024"
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
}

resource "aws_subnet" "public" {
  cidr_block = var.public_subnet_cidr
  vpc_id     = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id     = aws_vpc.main.id
  depends_on = [aws_internet_gateway.gw]
}

resource "aws_subnet" "private" {
  cidr_block = "10.0.2.0/24"
  vpc_id     = aws_vpc.main.id
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}

resource "aws_instance" "web" {
  ami           = "ami-12345678"
  subnet_id     = aws_subnet.public.id
  # TODO: Look up instance_type from var.instance_types for var.environment, falling back to "t3.nano"
  instance_type = "t3.nano"

  # TODO: Render userdata.sh.tftpl using templatefile with server_name = "${var.environment}-server"
  user_data     = ""

  # TODO: Merge standard tags { Name = "${var.environment}-web", Environment = var.environment } with var.extra_tags
  tags          = {}
}
