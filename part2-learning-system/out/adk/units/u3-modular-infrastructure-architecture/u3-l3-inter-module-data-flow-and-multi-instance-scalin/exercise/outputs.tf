output "vpc_id" {
  description = "The ID of the VPC"
  value       = module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = [module.vpc.public_subnet_id]
}

output "compute_instance_ids" {
  description = "Map of environment names to instance IDs"
  # TODO: Reference the instance_id from each instance in module.compute
  value = {}
}
