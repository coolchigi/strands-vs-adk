mock_provider "aws" {}

# Check 1: compute module receives subnet_ids from the networking module output
run "compute_receives_networking_subnet_ids" {
  command = apply

  assert {
    condition     = length(module.compute.instance_ids) == length(module.networking.subnet_ids)
    error_message = "The compute module must receive subnet_ids from module.networking.subnet_ids — the number of instances should equal the number of subnets."
  }
}

# Check 2: networking_subnet_ids root output re-exports the networking module output
run "root_output_networking_subnet_ids" {
  command = apply

  assert {
    condition     = output.networking_subnet_ids == module.networking.subnet_ids
    error_message = "Root output networking_subnet_ids must be set to module.networking.subnet_ids."
  }
}

# Check 3: root output compute_instance_ids re-exports the compute module output
run "root_output_compute_instance_ids" {
  command = apply

  assert {
    condition     = output.compute_instance_ids == module.compute.instance_ids
    error_message = "Root output compute_instance_ids must be set to module.compute.instance_ids."
  }
}

# Check 4: assets_bucket_id output addresses the for_each instance by key
run "assets_bucket_id_output" {
  command = apply

  assert {
    condition     = output.assets_bucket_id == module.storage["my-project-assets"].bucket_id
    error_message = "Root output assets_bucket_id must reference module.storage[\"my-project-assets\"].bucket_id."
  }
}

# Check 5: logs_bucket_id output addresses the for_each instance by key
run "logs_bucket_id_output" {
  command = apply

  assert {
    condition     = output.logs_bucket_id == module.storage["my-project-logs"].bucket_id
    error_message = "Root output logs_bucket_id must reference module.storage[\"my-project-logs\"].bucket_id."
  }
}

# Check 6: two storage instances are created (one per for_each key)
run "two_storage_instances" {
  command = apply

  assert {
    condition     = length(module.storage) == 2
    error_message = "The storage module must be called with for_each over both bucket names, producing exactly two instances."
  }
}
