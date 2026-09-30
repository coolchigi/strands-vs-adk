output "vpc_id" {
  description = "ID of the VPC created by this module."
  value       = aws_vpc.main.id
}

output "subnet_ids" {
  description = "List of public subnet IDs, one per availability zone."
  value       = aws_subnet.public[*].id
}

output "subnet_cidrs" {
  description = "List of public subnet CIDR blocks, one per availability zone."
  value       = aws_subnet.public[*].cidr_block
}
