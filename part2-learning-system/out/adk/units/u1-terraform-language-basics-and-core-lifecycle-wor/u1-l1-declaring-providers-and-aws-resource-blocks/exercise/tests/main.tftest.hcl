mock_provider "aws" {}

run "verify_vpc" {
  command = apply

  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "The aws_vpc resource named 'main' must have cidr_block set to '10.0.0.0/16'."
  }
}

run "verify_s3_bucket" {
  command = apply

  assert {
    condition     = aws_s3_bucket.data.bucket == "my-learning-bucket-2024"
    error_message = "The aws_s3_bucket resource named 'data' must have bucket set to 'my-learning-bucket-2024'."
  }
}
