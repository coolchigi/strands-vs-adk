mock_provider "aws" {}

run "name_prefix_local_used_in_bucket_tags" {
  command = apply

  variables {
    project     = "acme"
    environment = "staging"
  }

  assert {
    condition     = aws_s3_bucket.assets.tags["Project"] == "acme-staging"
    error_message = "aws_s3_bucket.assets is missing a Project tag equal to local.name_prefix (project-environment). Make sure you defined the name_prefix local and referenced it in the bucket's tags."
  }
}

run "name_prefix_local_used_in_instance_tags" {
  command = apply

  variables {
    project     = "acme"
    environment = "staging"
  }

  assert {
    condition     = aws_instance.app.tags["Project"] == "acme-staging"
    error_message = "aws_instance.app is missing a Project tag equal to local.name_prefix (project-environment). Make sure you defined the name_prefix local and referenced it in the instance's tags."
  }
}

run "name_prefix_changes_with_variables" {
  command = apply

  variables {
    project     = "beta"
    environment = "prod"
  }

  assert {
    condition     = aws_s3_bucket.assets.tags["Project"] == "beta-prod"
    error_message = "The Project tag on aws_s3_bucket.assets did not update when project and environment variables changed. Check that the local value uses var.project and var.environment, not hardcoded strings."
  }

  assert {
    condition     = aws_instance.app.tags["Project"] == "beta-prod"
    error_message = "The Project tag on aws_instance.app did not update when project and environment variables changed. Check that the local value uses var.project and var.environment, not hardcoded strings."
  }
}
