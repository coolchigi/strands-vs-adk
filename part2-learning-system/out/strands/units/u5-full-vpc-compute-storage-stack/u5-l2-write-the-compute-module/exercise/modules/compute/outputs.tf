# TODO: replace instance_id with instance_ids (value = aws_instance.app[*].id)
# TODO: add public_ips output        (value = aws_instance.app[*].public_ip)
output "instance_id" {
  description = "ID of the EC2 instance created by this module."
  value       = aws_instance.app.id
}
