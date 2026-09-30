mock_provider "aws" {}

# ── Part A: aws_subnet.public[0] must exist with the right type and provider ──
run "subnet_resource_exists" {
  command = apply

  assert {
    condition     = aws_subnet.public[0].id != ""
    error_message = "Part A: aws_subnet.public[0] was not found in state. Make sure you have run terraform apply so the state file is populated."
  }
}

# ── Part B: aws_subnet.public[0] references aws_vpc.main (vpc_id) ──
run "subnet_depends_on_vpc" {
  command = apply

  assert {
    condition     = aws_subnet.public[0].vpc_id == aws_vpc.main.id
    error_message = "Part B: The subnet's vpc_id does not match aws_vpc.main.id. The subnet must declare its dependency on the VPC through the vpc_id argument — check your main.tf."
  }
}

# ── Part B: aws_vpc.main has no dependency on the subnet ──
run "vpc_does_not_reference_subnet" {
  command = apply

  assert {
    condition     = aws_vpc.main.cidr_block != ""
    error_message = "Part B: aws_vpc.main could not be read. Ensure the VPC resource is present in main.tf."
  }
}

# ── Part C: cached cidr_block for subnet[0] is the computed result, not the expression ──
run "subnet_cidr_is_resolved" {
  command = apply

  assert {
    condition     = aws_subnet.public[0].cidr_block == cidrsubnet(var.vpc_cidr, 8, 0)
    error_message = "Part C: The cidr_block stored in state for aws_subnet.public[0] should equal cidrsubnet(var.vpc_cidr, 8, 0) — the resolved value, not the raw expression. Check that count.index 0 is used in your cidrsubnet call."
  }
}

# ── Part C: three subnets are created (one per AZ), confirming count works ──
run "three_subnets_created" {
  command = apply

  assert {
    condition     = length(aws_subnet.public) == 3
    error_message = "Part C: Expected 3 subnets (one per availability zone) but got a different number. Check the count argument in the aws_subnet resource."
  }
}

# ── Part D: instance exists so state is populated ──
run "instance_in_state" {
  command = apply

  assert {
    condition     = aws_instance.app.id != ""
    error_message = "Part D: aws_instance.app was not found in state. Run terraform apply so the state file records the instance before you explore the deletion scenario."
  }
}
