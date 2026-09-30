mock_provider "aws" {}

run "verify_vpc_references" {
  command = apply

  assert {
    condition     = aws_internet_gateway.gw.vpc_id == aws_vpc.main.id
    error_message = "aws_internet_gateway.gw must reference aws_vpc.main.id for its vpc_id."
  }

  assert {
    condition     = aws_subnet.public.vpc_id == aws_vpc.main.id
    error_message = "aws_subnet.public must reference aws_vpc.main.id for its vpc_id."
  }

  assert {
    condition     = aws_route_table.public.vpc_id == aws_vpc.main.id
    error_message = "aws_route_table.public must reference aws_vpc.main.id for its vpc_id."
  }
}
