output "networking_vpc_id" {
  description = "VPC ID from the networking module."
  value       = module.networking.vpc_id
}

output "networking_subnet_ids" {
  description = "Subnet IDs from the networking module."
  value       = module.networking.subnet_ids
}

# TODO: replace compute_instance_id with compute_instance_ids referencing module.compute.instance_ids
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
