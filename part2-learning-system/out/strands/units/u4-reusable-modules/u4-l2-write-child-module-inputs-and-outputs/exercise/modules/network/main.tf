resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
}

resource "aws_subnet" "main" {
  vpc_id = aws_vpc.main.id
  # TODO: set cidr_block using cidrsubnet(var.vpc_cidr, 8, 0)
}
