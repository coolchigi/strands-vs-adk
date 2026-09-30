mock_provider "aws" {}

# Check that the AMI has been changed to the replacement value.
run "instance_ami_forces_replacement" {
  command = apply

  assert {
    condition     = aws_instance.app.ami == "ami-0deadbeef00000000"
    error_message = "aws_instance.app.ami should be \"ami-0deadbeef00000000\". Change the ami argument in main.tf to \"ami-0deadbeef00000000\" to trigger a forced-replacement (-/+) in the plan."
  }
}

# Check that instance_type has been changed to t3.small via terraform.tfvars.
run "instance_type_updated" {
  command = apply

  assert {
    condition     = aws_instance.app.instance_type == "t3.small"
    error_message = "aws_instance.app.instance_type should be \"t3.small\". Set instance_type = \"t3.small\" in terraform.tfvars to observe the in-place update (~) in the plan."
  }
}

# Check that the two expected S3 buckets are present.
run "two_s3_buckets_present" {
  command = apply

  assert {
    condition     = length(aws_s3_bucket.env) == 2
    error_message = "Expected exactly 2 S3 buckets (logs and backups). Do not remove the for_each map in main.tf."
  }
}

# Check that three public subnets are declared.
run "three_subnets_declared" {
  command = apply

  assert {
    condition     = length(aws_subnet.public) == 3
    error_message = "Expected 3 public subnets (one per availability zone). Do not change the availability_zones variable."
  }
}

# Check that the instance_ami output exposes the correct value.
run "instance_ami_output" {
  command = apply

  assert {
    condition     = output.instance_ami == "ami-0deadbeef00000000"
    error_message = "The instance_ami output should equal \"ami-0deadbeef00000000\". Make sure the output is defined and the ami in main.tf is set correctly."
  }
}

# Check that the instance_type output exposes the correct value.
run "instance_type_output" {
  command = apply

  assert {
    condition     = output.instance_type == "t3.small"
    error_message = "The instance_type output should equal \"t3.small\". Make sure instance_type = \"t3.small\" is set in terraform.tfvars."
  }
}
