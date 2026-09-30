output "network_subnet_id" {
  description = "Subnet ID from the network module."
  value       = module.network.subnet_id
}

output "compute_instance_id" {
  description = "Instance ID from the compute module."
  value       = module.compute.instance_id
}

# TODO: Add an output named "assets_bucket_id" with value from
# the "my-project-assets" instance of module.storage.

# TODO: Add an output named "logs_bucket_id" with value from
# the "my-project-logs" instance of module.storage.
