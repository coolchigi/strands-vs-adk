mock_provider "aws" {}

run "verify_renamed_storage" {
  command = apply

  assert {
    condition     = aws_s3_bucket.storage.bucket == "my-learning-bucket-2024"
    error_message = "The aws_s3_bucket.storage resource must have bucket set to 'my-learning-bucket-2024'."
  }
}
