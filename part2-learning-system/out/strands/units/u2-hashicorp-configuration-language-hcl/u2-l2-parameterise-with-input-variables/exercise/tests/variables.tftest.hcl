mock_provider "aws" {}

# 1. The tfvars override reaches the bucket resource
run "tfvars_bucket_name_is_used" {
  command = apply

  assert {
    condition     = aws_s3_bucket.assets.bucket == "my-learn-assets-2024"
    error_message = "Expected aws_s3_bucket.assets.bucket to be 'my-learn-assets-2024' (set in terraform.tfvars), but got a different value. Make sure var.bucket_name is used in main.tf and terraform.tfvars sets bucket_name = \"my-learn-assets-2024\"."
  }
}

# 2. The -var flag overrides the tfvars value (proves var.bucket_name is wired up)
run "var_flag_overrides_tfvars" {
  command = apply

  variables {
    bucket_name = "override-bucket"
  }

  assert {
    condition     = aws_s3_bucket.assets.bucket == "override-bucket"
    error_message = "Expected aws_s3_bucket.assets.bucket to equal the value supplied via variables block ('override-bucket'). Make sure main.tf uses var.bucket_name for the bucket argument."
  }
}

# 3. The instance_type variable reaches the instance resource
run "instance_type_variable_is_used" {
  command = apply

  variables {
    instance_type = "t3.small"
  }

  assert {
    condition     = aws_instance.app.instance_type == "t3.small"
    error_message = "Expected aws_instance.app.instance_type to be 't3.small'. Make sure main.tf uses var.instance_type for the instance_type argument."
  }
}

# 4. The default for instance_type is t3.micro
run "instance_type_default_is_t3_micro" {
  command = apply

  assert {
    condition     = var.instance_type == "t3.micro"
    error_message = "Expected the default value of var.instance_type to be 't3.micro'. Check the default argument in variables.tf."
  }
}

# 5. Validation rejects an empty bucket_name
run "empty_bucket_name_is_rejected" {
  command = plan

  variables {
    bucket_name = ""
  }

  expect_failures = [var.bucket_name]
}
