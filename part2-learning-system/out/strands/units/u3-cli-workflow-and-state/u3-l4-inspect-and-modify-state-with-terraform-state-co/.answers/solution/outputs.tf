output "bucket_ids" {
  description = "IDs of all env S3 buckets"
  value       = [for b in aws_s3_bucket.env : b.id]
}

output "instance_id" {
  description = "ID of the EC2 application instance"
  value       = aws_instance.app.id
}

output "subnet_ids" {
  description = "IDs of all public subnets"
  value       = aws_subnet.public[*].id
}
