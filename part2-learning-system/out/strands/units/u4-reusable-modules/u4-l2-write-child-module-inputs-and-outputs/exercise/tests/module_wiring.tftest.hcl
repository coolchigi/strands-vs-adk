mock_provider "aws" {}

# Check 1: network module exposes a non-empty subnet_id output
run "network_module_exposes_subnet_id" {
  command = apply

  assert {
    condition     = module.network.subnet_id != ""
    error_message = "module.network.subnet_id is empty — make sure modules/network/outputs.tf declares an output named 'subnet_id' with value aws_subnet.main.id."
  }
}

# Check 2: compute module exposes a non-empty instance_id output
run "compute_module_exposes_instance_id" {
  command = apply

  assert {
    condition     = module.compute.instance_id != ""
    error_message = "module.compute.instance_id is empty — make sure modules/compute/outputs.tf declares an output named 'instance_id' with value aws_instance.app.id."
  }
}

# Check 3: root outputs surface the child module values
run "root_outputs_surface_module_values" {
  command = apply

  assert {
    condition     = output.network_subnet_id == module.network.subnet_id
    error_message = "output.network_subnet_id does not equal module.network.subnet_id — add 'output network_subnet_id' with value = module.network.subnet_id in root outputs.tf."
  }

  assert {
    condition     = output.compute_instance_id == module.compute.instance_id
    error_message = "output.compute_instance_id does not equal module.compute.instance_id — add 'output compute_instance_id' with value = module.compute.instance_id in root outputs.tf."
  }
}

# Check 4: network module uses var.vpc_cidr to derive the subnet CIDR
# cidrsubnet("10.0.0.0/16", 8, 0) == "10.0.0.0/24"
# A hard-coded cidr_block would produce a different value here.
run "network_module_derives_cidr_from_vpc_cidr" {
  command = apply

  assert {
    condition     = module.network.subnet_cidr == cidrsubnet("10.0.0.0/16", 8, 0)
    error_message = "module.network.subnet_cidr is not derived from var.vpc_cidr — set aws_subnet.main.cidr_block = cidrsubnet(var.vpc_cidr, 8, 0) in modules/network/main.tf, and expose it via an output named 'subnet_cidr'."
  }
}

# Check 5: compute module passes the subnet_id through to the instance
run "compute_module_uses_subnet_id_variable" {
  command = apply

  assert {
    condition     = module.compute.instance_id != ""
    error_message = "compute instance was not created — make sure aws_instance.app in modules/compute/main.tf sets subnet_id = var.subnet_id."
  }

  assert {
    condition     = module.network.subnet_id != ""
    error_message = "network subnet_id is empty — the compute module cannot receive a valid subnet_id if the network module does not expose one."
  }
}
