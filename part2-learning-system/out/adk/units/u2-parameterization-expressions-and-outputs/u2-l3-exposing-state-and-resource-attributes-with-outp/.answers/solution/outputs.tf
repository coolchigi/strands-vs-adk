output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "db_token" {
  description = "Database credentials token"
  value       = "supersecret-token-123"
  sensitive   = true
}