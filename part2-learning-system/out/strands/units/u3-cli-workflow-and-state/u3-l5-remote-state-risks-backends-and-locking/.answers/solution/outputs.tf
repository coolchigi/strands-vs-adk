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

# ---------------------------------------------------------------------------
# These outputs expose the S3 backend configuration so that terraform test
# can assert on the values. They are only needed while learning.
# ---------------------------------------------------------------------------
output "backend_bucket" {
  description = "S3 backend bucket name (used by tests)"
  value       = "my-company-tf-state"
}

output "backend_key" {
  description = "S3 backend key (used by tests)"
  value       = "myproject/dev/terraform.tfstate"
}

output "backend_region" {
  description = "S3 backend region (used by tests)"
  value       = "us-east-1"
}

output "backend_dynamodb_table" {
  description = "DynamoDB lock table name (used by tests)"
  value       = "my-company-tf-locks"
}

output "backend_encrypt" {
  description = "S3 backend encryption flag (used by tests)"
  value       = true
}
