mock_provider "aws" {}

# Check that the aws_subnet.public resource exists with the correct CIDR
run "subnet_cidr_is_computed_correctly" {
  command = apply

  assert {
    condition     = aws_subnet.public.cidr_block == cidrsubnet(var.vpc_cidr, 8, 1)
    error_message = "aws_subnet.public.cidr_block should be cidrsubnet(var.vpc_cidr, 8, 1), which is 10.0.1.0/24 for the default vpc_cidr. Make sure you used cidrsubnet(var.vpc_cidr, 8, 1) in the cidr_block argument."
  }
}

# Check that the subnet references the VPC id (implicit dependency)
run "subnet_references_vpc_id" {
  command = apply

  assert {
    condition     = aws_subnet.public.vpc_id == aws_vpc.main.id
    error_message = "aws_subnet.public.vpc_id should reference aws_vpc.main.id using dot-notation. Make sure vpc_id = aws_vpc.main.id is set in the aws_subnet.public resource block."
  }
}

# Check that subnet_count local equals the length of availability_zones
run "subnet_count_local_uses_length" {
  command = apply

  assert {
    condition     = local.subnet_count == length(var.availability_zones)
    error_message = "local.subnet_count should equal length(var.availability_zones). Add subnet_count = length(var.availability_zones) inside the locals block in locals.tf."
  }
}

# Check that the subnet_id output exists and equals aws_subnet.public.id
run "subnet_id_output_is_correct" {
  command = apply

  assert {
    condition     = output.subnet_id == aws_subnet.public.id
    error_message = "The output named subnet_id should have value = aws_subnet.public.id. Make sure you declared it in outputs.tf."
  }
}
