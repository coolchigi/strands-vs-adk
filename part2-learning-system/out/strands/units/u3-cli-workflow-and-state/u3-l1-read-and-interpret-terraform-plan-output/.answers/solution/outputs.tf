output "bucket_ids" {
  description = "IDs of all env S3 buckets"
  value       = [for b in aws_s3_bucket.env : b.id]
}

output "instance_id" {
  description = "ID of the EC2 application instance"
  value       = aws_instance.app.id
}

output "app_secret" {
  description = "Simulated application secret token (sensitive)"
  value       = "s3cr3t-token-abc123"
  sensitive   = true
}

output "subnet_ids" {
  description = "IDs of all public subnets"
  value       = aws_subnet.public[*].id
}

output "instance_ami" {
  description = "AMI used by the application instance"
  value       = aws_instance.app.ami
}

output "instance_type" {
  description = "Instance type used by the application instance"
  value       = aws_instance.app.instance_type
}
