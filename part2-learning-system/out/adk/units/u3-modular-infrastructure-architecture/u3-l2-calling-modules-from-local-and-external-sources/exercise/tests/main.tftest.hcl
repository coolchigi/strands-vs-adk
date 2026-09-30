mock_provider "aws" {}

run "verify_module_wiring" {
  command = apply

  assert {
    condition     = module.vpc.vpc_cidr == var.vpc_cidr
    error_message = "The vpc module vpc_cidr must be set to var.vpc_cidr."
  }

  assert {
    condition     = module.vpc.public_subnet_cidr == var.public_subnet_cidr
    error_message = "The vpc module public_subnet_cidr must be set to var.public_subnet_cidr."
  }

  assert {
    condition     = aws_instance.web.subnet_id == module.vpc.public_subnet_id
    error_message = "The web instance subnet_id must equal module.vpc.public_subnet_id."
  }
}
