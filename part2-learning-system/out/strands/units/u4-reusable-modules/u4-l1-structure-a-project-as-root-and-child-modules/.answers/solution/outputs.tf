output "logs_bucket_id" {
  description = "ID of the logs S3 bucket."
  value       = module.logs.bucket_id
}

output "backups_bucket_id" {
  description = "ID of the backups S3 bucket."
  value       = module.backups.bucket_id
}

output "instance_id" {
  description = "ID of the EC2 application instance"
  value       = aws_instance.app.id
}

output "subnet_ids" {
  description = "IDs of all public subnets"
  value       = aws_subnet.public[*].id
}

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

output "aws_provider_version_constraint" {
  description = "AWS provider version constraint (used by tests)"
  value       = "~> 6.0"
}
