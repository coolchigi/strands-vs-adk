output "bucket_id" {
  description = "Name (id) of the S3 assets bucket"
  value       = aws_s3_bucket.assets.id
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

output "subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public.id
}
