mock_provider "aws" {}

# Two instances should be created (one per subnet in the networking module).
run "two_instances_created" {
  command = apply

  assert {
    condition     = length(module.compute.instance_ids) == 2
    error_message = "Expected 2 instance IDs (one per subnet), but got ${length(module.compute.instance_ids)}. Make sure count = length(var.subnet_ids) is set in modules/compute/main.tf."
  }
}

# The two instances should be in different subnets.
run "instances_in_different_subnets" {
  command = apply

  assert {
    condition     = module.compute.instance_ids[0] != module.compute.instance_ids[1]
    error_message = "Expected two distinct instance IDs, but they are the same. Check that count.index is used in subnet_id assignment."
  }
}

# The root output should be named compute_instance_ids (plural).
run "root_output_is_instance_ids" {
  command = apply

  assert {
    condition     = length(output.compute_instance_ids) == 2
    error_message = "Root output compute_instance_ids should be a list of 2 IDs. Rename compute_instance_id to compute_instance_ids and point it at module.compute.instance_ids."
  }
}

# instance_type variable should be declared and default to t3.micro.
run "instance_type_variable_has_default" {
  command = apply

  assert {
    condition     = module.compute.instance_type_used == "t3.micro"
    error_message = "Expected instance_type to default to t3.micro. Declare it in modules/compute/variables.tf with default = \"t3.micro\"."
  }
}

# public_ips output should exist and have 2 entries.
run "public_ips_output_exists" {
  command = apply

  assert {
    condition     = length(module.compute.public_ips) == 2
    error_message = "Expected public_ips output with 2 entries. Add it to modules/compute/outputs.tf using aws_instance.app[*].public_ip."
  }
}
