mock_provider "aws" {}

run "bucket_id_output_exists" {
  command = apply

  assert {
    condition     = output.bucket_id != ""
    error_message = "The bucket_id output is missing or empty. Add an output block named bucket_id with value = aws_s3_bucket.assets.id."
  }
}

run "instance_id_output_exists" {
  command = apply

  assert {
    condition     = output.instance_id != ""
    error_message = "The instance_id output is missing or empty. Add an output block named instance_id with value = aws_instance.app.id."
  }
}

run "app_secret_output_value" {
  command = apply

  assert {
    condition     = nonsensitive(output.app_secret) == "s3cr3t-token-abc123"
    error_message = "The app_secret output is missing or has the wrong value. Its value should be the string literal \"s3cr3t-token-abc123\"."
  }
}
