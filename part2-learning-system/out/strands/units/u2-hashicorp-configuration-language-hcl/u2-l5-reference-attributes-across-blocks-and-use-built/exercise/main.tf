resource "aws_s3_bucket" "assets" {
  bucket = var.bucket_name

  tags = {
    Project = local.name_prefix
  }
}

resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type

  lifecycle {
    create_before_destroy = true
  }

  tags = {
    Project = local.name_prefix
  }
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr

  tags = {
    Project = local.name_prefix
  }
}

# TODO: add aws_subnet "public" resource
#   - vpc_id     = <reference aws_vpc.main.id>
#   - cidr_block = <cidrsubnet(var.vpc_cidr, 8, 1)>
