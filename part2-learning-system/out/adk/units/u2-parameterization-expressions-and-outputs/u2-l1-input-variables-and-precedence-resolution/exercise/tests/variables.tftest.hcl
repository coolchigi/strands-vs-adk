mock_provider "aws" {}

run "validate_vpc_cidr_invalid" {
  command = plan
  variables {
    vpc_cidr = "not-a-valid-cidr"
  }
  expect_failures = [
    var.vpc_cidr,
  ]
}

run "validate_public_subnet_cidr_invalid" {
  command = plan
  variables {
    public_subnet_cidr = "not-a-valid-cidr"
  }
  expect_failures = [
    var.public_subnet_cidr,
  ]
}

run "verify_vpc_uses_variable" {
  command = apply
  variables {
    vpc_cidr = "10.50.0.0/16"
  }
  assert {
    condition     = aws_vpc.main.cidr_block == "10.50.0.0/16"
    error_message = "aws_vpc.main.cidr_block does not reference var.vpc_cidr."
  }
}

run "verify_public_subnet_uses_variable" {
  command = apply
  variables {
    public_subnet_cidr = "10.0.99.0/24"
  }
  assert {
    condition     = aws_subnet.public.cidr_block == "10.0.99.0/24"
    error_message = "aws_subnet.public.cidr_block does not reference var.public_subnet_cidr."
  }
}
