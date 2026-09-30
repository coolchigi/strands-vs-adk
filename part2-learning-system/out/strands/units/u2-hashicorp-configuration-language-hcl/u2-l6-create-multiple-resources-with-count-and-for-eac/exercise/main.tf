# TODO: Replace this single aws_s3_bucket.assets block with an aws_s3_bucket.env
# resource that uses for_each over a map:
#   { logs = "access-logs", backups = "nightly-backups" }
# Set bucket = each.key and a tag Purpose = each.value.
resource "aws_s3_bucket" "assets" {
  bucket = "placeholder-remove-me"

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

# TODO: Replace this single aws_subnet.public block with one that uses
# count = length(var.availability_zones).
# Use cidrsubnet(var.vpc_cidr, 8, count.index) for the cidr_block.
# Use var.availability_zones[count.index] for the availability_zone.
resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id
  cidr_block = cidrsubnet(var.vpc_cidr, 8, 1)

  tags = {
    Project = local.name_prefix
  }
}
