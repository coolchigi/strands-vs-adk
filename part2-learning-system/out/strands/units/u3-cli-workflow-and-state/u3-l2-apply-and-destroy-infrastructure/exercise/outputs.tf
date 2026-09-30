# TODO: declare an output named "bucket_ids" that outputs the IDs of all env S3 buckets
# (value: a list comprehension over aws_s3_bucket.env yielding each bucket's .id)

# TODO: declare an output named "instance_id" that outputs the ID of the EC2 application instance
# (value: aws_instance.app.id)

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
