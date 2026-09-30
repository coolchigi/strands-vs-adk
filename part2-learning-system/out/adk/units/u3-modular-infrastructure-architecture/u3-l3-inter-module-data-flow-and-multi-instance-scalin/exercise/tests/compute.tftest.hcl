mock_provider "aws" {}

run "verify_compute_module" {
  command = apply

  assert {
    condition     = length(module.compute) == 2
    error_message = "module.compute must be instantiated for each environment in var.instance_types (expected 2 instances)."
  }

  assert {
    condition     = module.compute["dev"].subnet_id == module.vpc.public_subnet_id
    error_message = "module.compute must receive subnet_id from module.vpc.public_subnet_id."
  }

  assert {
    condition     = module.compute["dev"].instance_type == "t3.micro" && module.compute["prod"].instance_type == "t3.large"
    error_message = "module.compute instances must set instance_type from each.value (t3.micro for dev, t3.large for prod)."
  }

  assert {
    condition     = module.compute["dev"].instance_id != "" && module.compute["prod"].instance_id != ""
    error_message = "modules/compute must export instance_id containing the instance ID."
  }

  assert {
    condition     = length(output.compute_instance_ids) == 2 && output.compute_instance_ids["dev"] == module.compute["dev"].instance_id
    error_message = "Root output compute_instance_ids must map each environment to its compute instance ID."
  }
}
