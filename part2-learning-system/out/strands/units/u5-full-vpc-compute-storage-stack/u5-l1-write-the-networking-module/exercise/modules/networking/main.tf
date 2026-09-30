resource "aws_vpc" "main" {
  # TODO: set cidr_block from the vpc_cidr variable
}

resource "aws_subnet" "public" {
  # TODO: set count to the number of availability zones
  vpc_id = aws_vpc.main.id
  # TODO: derive cidr_block with cidrsubnet using vpc_cidr, newbits=8, and count.index
  # TODO: set availability_zone from the availability_zones variable using count.index
}

resource "aws_internet_gateway" "main" {
  # TODO: attach to the VPC by setting vpc_id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    # TODO: set gateway_id to the internet gateway's id
  }
}

resource "aws_route_table_association" "public" {
  # TODO: set count to match the number of subnets
  # TODO: set subnet_id from the public subnet at count.index
  route_table_id = aws_route_table.public.id
}
