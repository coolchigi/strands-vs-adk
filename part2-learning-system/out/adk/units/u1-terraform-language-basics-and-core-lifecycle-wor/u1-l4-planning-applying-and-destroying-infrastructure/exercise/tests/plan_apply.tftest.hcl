mock_provider "aws" {}

run "verify_route_table_association" {
  command = apply

  assert {
    condition     = aws_route_table_association.public.subnet_id == aws_subnet.public.id
    error_message = "The public route table association must reference aws_subnet.public.id as its subnet_id."
  }

  assert {
    condition     = aws_route_table_association.public.route_table_id == aws_route_table.public.id
    error_message = "The public route table association must reference aws_route_table.public.id as its route_table_id."
  }
}
