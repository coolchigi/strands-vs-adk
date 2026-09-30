mock_provider "aws" {}

# Verify the AWS provider version constraint has been restored to ~> 6.0.
run "aws_provider_version_constraint_restored" {
  command = apply

  assert {
    condition     = output.aws_provider_version_constraint == "~> 6.0"
    error_message = "The AWS provider version constraint in outputs.tf must be \"~> 6.0\". Did you restore the constraint in terraform.tf and update the output to match?"
  }
}
