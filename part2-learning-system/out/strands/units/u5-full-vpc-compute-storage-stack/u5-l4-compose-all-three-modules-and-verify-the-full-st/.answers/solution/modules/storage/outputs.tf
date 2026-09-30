output "bucket_id" {
  description = "Name (id) of the S3 bucket."
  value       = aws_s3_bucket.main.bucket

  precondition {
    condition     = var.bucket_name != ""
    error_message = "bucket_name must not be empty."
  }
}

output "bucket_arn" {
  description = "ARN of the S3 bucket."
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain" {
  description = "Domain name of the S3 bucket."
  value       = aws_s3_bucket.main.bucket_domain_name
}
