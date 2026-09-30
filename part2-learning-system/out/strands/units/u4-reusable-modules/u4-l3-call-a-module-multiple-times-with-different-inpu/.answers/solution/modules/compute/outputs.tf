output "instance_id" {
  description = "ID of the EC2 instance created by this module."
  value       = aws_instance.app.id
}
