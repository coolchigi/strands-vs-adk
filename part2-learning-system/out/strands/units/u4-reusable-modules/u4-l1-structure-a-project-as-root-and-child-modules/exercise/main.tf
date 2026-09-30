# TODO: Add a module block named "logs" that sources "./modules/storage"
#       and passes bucket_name = "access-logs"

# TODO: Add a module block named "backups" that sources "./modules/storage"
#       and passes bucket_name = "nightly-backups"

resource "aws_instance" "app" {
  ami           = "ami-0deadbeef00000000"
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

resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name    = "public-${count.index}"
    Project = local.name_prefix
  }
}
