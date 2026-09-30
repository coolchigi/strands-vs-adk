output "instance_ids" {
  description = "List of IDs of the EC2 instances created by this module."
  value       = aws_instance.app[*].id
}

output "public_ips" {
  description = "List of public IP addresses of the EC2 instances."
  value       = aws_instance.app[*].public_ip
}

output "instance_type_used" {
  description = "Instance type used for all instances in this module."
  value       = var.instance_type
}
