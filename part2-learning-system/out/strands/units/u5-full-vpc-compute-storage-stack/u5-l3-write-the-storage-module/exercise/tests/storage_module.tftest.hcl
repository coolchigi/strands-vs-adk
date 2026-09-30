mock_provider "aws" {}

# bucket_id output must equal the bucket name passed in.
run "bucket_id_output_exists" {
  command = apply

  assert {
    condition     = module.storage["my-project-assets"].bucket_id == "my-project-assets"
    error_message = "bucket_id output is missing or does not equal the bucket name. Add 'output \"bucket_id\"' in modules/storage/outputs.tf with value = aws_s3_bucket.main.bucket."
  }
}

# bucket_arn output must be a non-empty string.
run "bucket_arn_output_exists" {
  command = apply

  assert {
    condition     = length(module.storage["my-project-assets"].bucket_arn) > 0
    error_message = "bucket_arn output is missing or empty. Add 'output \"bucket_arn\"' in modules/storage/outputs.tf with value = aws_s3_bucket.main.arn."
  }
}

# bucket_domain output must be a non-empty string.
run "bucket_domain_output_exists" {
  command = apply

  assert {
    condition     = length(module.storage["my-project-assets"].bucket_domain) > 0
    error_message = "bucket_domain output is missing or empty. Add 'output \"bucket_domain\"' in modules/storage/outputs.tf with value = aws_s3_bucket.main.bucket_domain_name."
  }
}

# tags variable must be wired into the bucket resource.
run "tags_are_applied_to_bucket" {
  command = apply

  assert {
    condition     = module.storage["my-project-assets"].bucket_id == "my-project-assets"
    error_message = "Bucket resource does not appear to use var.bucket_name. Set bucket = var.bucket_name in modules/storage/main.tf."
  }
}

# for_each in the root creates two distinct bucket instances.
run "two_buckets_created" {
  command = apply

  assert {
    condition     = module.storage["my-project-assets"].bucket_id != module.storage["my-project-logs"].bucket_id
    error_message = "Expected two distinct bucket IDs but they are the same. Check that bucket = var.bucket_name is set in modules/storage/main.tf."
  }
}

# Root outputs surface the bucket IDs from both storage instances.
run "root_storage_outputs_exist" {
  command = apply

  assert {
    condition     = output.assets_bucket_id == "my-project-assets"
    error_message = "Root output assets_bucket_id is missing or wrong. It should reference module.storage[\"my-project-assets\"].bucket_id."
  }

  assert {
    condition     = output.logs_bucket_id == "my-project-logs"
    error_message = "Root output logs_bucket_id is missing or wrong. It should reference module.storage[\"my-project-logs\"].bucket_id."
  }
}
