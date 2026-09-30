output "vpc_id" {
  description = "The ID of the VPC"
  # TODO: Output the VPC ID from aws_vpc.main
  value       = ""
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  # TODO: Output public subnet IDs using splat syntax aws_subnet.public[*].id
  value       = []
}

output "db_token" {
  description = "Database credentials token"
  # TODO: Set value to "supersecret-token-123" and mark sensitive = true
  value       = ""
  sensitive   = false
}