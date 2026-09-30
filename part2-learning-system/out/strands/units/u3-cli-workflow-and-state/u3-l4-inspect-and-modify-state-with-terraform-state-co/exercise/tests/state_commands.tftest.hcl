mock_provider "aws" {}

# Verify both S3 buckets are declared
run "both_buckets_exist" {
  command = apply

  assert {
    condition     = contains(keys(aws_s3_bucket.env), "logs")
    error_message = "aws_s3_bucket.env must have a 'logs' key in its for_each map."
  }

  assert {
    condition     = contains(keys(aws_s3_bucket.env), "backups")
    error_message = "aws_s3_bucket.env must have a 'backups' key in its for_each map."
  }
}

# Verify the bucket names match the for_each keys
run "bucket_names_match_keys" {
  command = apply

  assert {
    condition     = aws_s3_bucket.env["logs"].bucket == "logs"
    error_message = "The 'logs' bucket must have bucket = \"logs\"."
  }

  assert {
    condition     = aws_s3_bucket.env["backups"].bucket == "backups"
    error_message = "The 'backups' bucket must have bucket = \"backups\"."
  }
}

# Verify bucket tags are set correctly
run "bucket_tags_correct" {
  command = apply

  assert {
    condition     = aws_s3_bucket.env["logs"].tags["Purpose"] == "access-logs"
    error_message = "The 'logs' bucket must have tag Purpose = \"access-logs\"."
  }

  assert {
    condition     = aws_s3_bucket.env["backups"].tags["Purpose"] == "nightly-backups"
    error_message = "The 'backups' bucket must have tag Purpose = \"nightly-backups\"."
  }
}

# Verify three subnets are declared
run "three_subnets_declared" {
  command = apply

  assert {
    condition     = length(aws_subnet.public) == 3
    error_message = "There must be exactly 3 aws_subnet.public instances (one per availability zone)."
  }
}

# Verify the VPC is declared with the correct CIDR
run "vpc_cidr_correct" {
  command = apply

  assert {
    condition     = aws_vpc.main.cidr_block == "10.0.0.0/16"
    error_message = "aws_vpc.main must have cidr_block = \"10.0.0.0/16\"."
  }
}

# Verify the bucket_ids output iterates over all buckets
run "bucket_ids_output_has_two_entries" {
  command = apply

  assert {
    condition     = length(output.bucket_ids) == 2
    error_message = "The bucket_ids output must contain exactly 2 entries, one per S3 bucket. Use a for expression: [for b in aws_s3_bucket.env : b.id]"
  }
}

# Verify subnet_ids output covers all three subnets
run "subnet_ids_output_has_three_entries" {
  command = apply

  assert {
    condition     = length(output.subnet_ids) == 3
    error_message = "The subnet_ids output must contain exactly 3 entries, one per public subnet."
  }
}

# Verify instance_id output is wired to the app instance
run "instance_id_output_present" {
  command = apply

  assert {
    condition     = output.instance_id == aws_instance.app.id
    error_message = "The instance_id output must equal aws_instance.app.id."
  }
}
