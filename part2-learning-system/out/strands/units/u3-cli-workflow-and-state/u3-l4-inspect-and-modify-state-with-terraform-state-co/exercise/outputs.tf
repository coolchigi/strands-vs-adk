output "bucket_ids" {
  description = "IDs of all env S3 buckets"
  # TODO: output the id of every bucket in aws_s3_bucket.env as a list
  # Hint: use a for expression over aws_s3_bucket.env
  value = null
}

output "instance_id" {
  description = "ID of the EC2 application instance"
  value       = aws_instance.app.id
}

output "subnet_ids" {
  description = "IDs of all public subnets"
  value       = aws_subnet.public[*].id
}
