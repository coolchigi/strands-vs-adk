mock_provider "aws" {}

run "verify_private_subnet" {
  command = apply

  assert {
    condition     = aws_subnet.private.cidr_block == "10.0.2.0/24"
    error_message = "The private subnet cidr_block must be configured as 10.0.2.0/24."
  }

  assert {
    condition     = aws_subnet.private.vpc_id == aws_vpc.main.id
    error_message = "The private subnet vpc_id must reference aws_vpc.main.id."
  }
}
