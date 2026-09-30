mock_provider "aws" {}

run "bucket_ids_output_exists" {
  command = apply

  assert {
    condition     = length(output.bucket_ids) == 2
    error_message = "The 'bucket_ids' output must contain exactly two entries, one for each aws_s3_bucket.env bucket (logs and backups)."
  }
}

run "instance_id_output_exists" {
  command = apply

  assert {
    condition     = output.instance_id != ""
    error_message = "The 'instance_id' output must be declared and return the ID of aws_instance.app."
  }
}

run "subnet_ids_output_has_three_entries" {
  command = apply

  assert {
    condition     = length(output.subnet_ids) == 3
    error_message = "The 'subnet_ids' output must contain three entries, one per availability zone."
  }
}

run "instance_type_output_reflects_tfvars" {
  command = apply

  assert {
    condition     = output.instance_type == "t3.small"
    error_message = "The 'instance_type' output must equal 't3.small' as set in terraform.tfvars."
  }
}
