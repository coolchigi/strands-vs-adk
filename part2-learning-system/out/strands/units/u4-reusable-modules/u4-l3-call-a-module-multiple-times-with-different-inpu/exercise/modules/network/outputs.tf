output "subnet_id" {
  description = "ID of the subnet created by this module."
  value       = aws_subnet.main.id
}

output "subnet_cidr" {
  description = "CIDR block of the subnet created by this module."
  value       = aws_subnet.main.cidr_block
}
