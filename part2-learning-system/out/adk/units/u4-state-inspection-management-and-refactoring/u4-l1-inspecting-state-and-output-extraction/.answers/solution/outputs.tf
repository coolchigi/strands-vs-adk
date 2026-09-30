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
  value       = { for env, mod in module.compute : env => mod.instance_id }
}

output "vpc_cidr" {
  description = "The CIDR block of the VPC"
  value       = module.vpc.vpc_cidr
}

output "api_token" {
  description = "Sensitive API token"
  value       = var.api_token
  sensitive   = true
}
