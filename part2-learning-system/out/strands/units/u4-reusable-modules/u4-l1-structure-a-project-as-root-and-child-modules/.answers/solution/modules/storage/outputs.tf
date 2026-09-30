output "bucket_id" {
  description = "The ID of the S3 bucket created by this module."
  value       = aws_s3_bucket.this.id
}
