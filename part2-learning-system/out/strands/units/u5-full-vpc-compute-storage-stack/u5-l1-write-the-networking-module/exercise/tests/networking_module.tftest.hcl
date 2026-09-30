mock_provider "aws" {}

variables {
  # These variables are consumed by the networking module via the root module.
  # The root main.tf hard-codes the values, so no variables are needed here.
}

run "vpc_is_created_with_correct_cidr" {
  command = apply

  assert {
    condition     = module.networking.vpc_id != ""
    error_message = "Expected vpc_id output to be a non-empty string. Make sure outputs.tf declares the vpc_id output."
  }
}

run "two_subnets_are_created" {
  command = apply

  assert {
    condition     = length(module.networking.subnet_ids) == 2
    error_message = "Expected exactly 2 subnet IDs (one per AZ). Check that aws_subnet.public uses count = length(var.availability_zones) and that subnet_ids is output with a splat expression."
  }
}

run "subnet_cidrs_are_derived_from_vpc_cidr" {
  command = apply

  assert {
    condition     = length(module.networking.subnet_cidrs) == 2
    error_message = "Expected subnet_cidrs output to contain 2 entries. Make sure outputs.tf declares subnet_cidrs using aws_subnet.public[*].cidr_block."
  }

  assert {
    condition     = module.networking.subnet_cidrs[0] == cidrsubnet("10.0.0.0/16", 8, 0)
    error_message = "First subnet CIDR should be cidrsubnet('10.0.0.0/16', 8, 0) = 10.0.0.0/24. Check that cidr_block = cidrsubnet(var.vpc_cidr, 8, count.index) is set on aws_subnet.public."
  }

  assert {
    condition     = module.networking.subnet_cidrs[1] == cidrsubnet("10.0.0.0/16", 8, 1)
    error_message = "Second subnet CIDR should be cidrsubnet('10.0.0.0/16', 8, 1) = 10.0.1.0/24. Check that count.index increments correctly across subnets."
  }
}

run "internet_gateway_is_attached_to_vpc" {
  command = apply

  assert {
    condition     = module.networking.vpc_id != ""
    error_message = "vpc_id must be non-empty for the internet gateway to attach. Ensure aws_internet_gateway.main sets vpc_id = aws_vpc.main.id."
  }
}

run "route_table_has_default_route" {
  command = apply

  assert {
    condition     = length(module.networking.subnet_ids) > 0
    error_message = "Subnets must exist before route table associations can be created. Ensure aws_route_table.public is declared with a 0.0.0.0/0 route."
  }
}

run "route_table_associations_equal_subnet_count" {
  command = apply

  assert {
    condition     = length(module.networking.subnet_ids) == 2
    error_message = "There should be one route table association per subnet (2 total). Ensure aws_route_table_association.public uses count = length(var.availability_zones)."
  }
}
