output "network_subnet_id" {
  description = "Subnet ID from the network module."
  value       = module.network.subnet_id
}

output "compute_instance_id" {
  description = "Instance ID from the compute module."
  value       = module.compute.instance_id
}

output "assets_bucket_id" {
  description = "Bucket ID for my-project-assets."
  value       = module.storage["my-project-assets"].bucket_id
}

output "logs_bucket_id" {
  description = "Bucket ID for my-project-logs."
  value       = module.storage["my-project-logs"].bucket_id
}
