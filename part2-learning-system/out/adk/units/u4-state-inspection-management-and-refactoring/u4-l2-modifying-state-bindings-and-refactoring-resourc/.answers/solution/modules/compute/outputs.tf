output "instance_id" {
  description = "The ID of the compute instance"
  value       = aws_instance.web.id
}

output "subnet_id" {
  description = "The subnet ID where the instance is deployed"
  value       = aws_instance.web.subnet_id
}

output "instance_type" {
  description = "The instance type of the compute instance"
  value       = aws_instance.web.instance_type
}
