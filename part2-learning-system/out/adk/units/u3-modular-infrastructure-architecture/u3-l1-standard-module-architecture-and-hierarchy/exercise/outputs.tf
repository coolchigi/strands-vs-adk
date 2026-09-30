output "vpc_id" {
  description = "The ID of the VPC"
  value       = "" # TODO: Export module.vpc.vpc_id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = [] # TODO: Export [module.vpc.public_subnet_id]
}

output "db_token" {
  description = "Database credentials token"
  value       = "supersecret-token-123"
  sensitive   = true
}
