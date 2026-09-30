output "bucket_id" {
  description = "ID of the S3 bucket created by this module."
  value       = aws_s3_bucket.main.id
}
