mock_provider "aws" {}

run "verify_vpc_module" {
  command = apply

  assert {
    condition     = module.vpc.vpc_id != ""
    error_message = "VPC module output vpc_id must not be empty"
  }

  assert {
    condition     = module.vpc.public_subnet_id != ""
    error_message = "VPC module output public_subnet_id must not be empty"
  }

  assert {
    condition     = aws_instance.web.subnet_id == module.vpc.public_subnet_id && aws_instance.web.subnet_id != ""
    error_message = "aws_instance.web subnet_id must match module.vpc.public_subnet_id"
  }

  assert {
    condition     = output.vpc_id == module.vpc.vpc_id && output.vpc_id != ""
    error_message = "Root output vpc_id must match module.vpc.vpc_id"
  }

  assert {
    condition     = length(output.public_subnet_ids) > 0 && output.public_subnet_ids[0] == module.vpc.public_subnet_id
    error_message = "Root output public_subnet_ids must contain module.vpc.public_subnet_id"
  }
}
