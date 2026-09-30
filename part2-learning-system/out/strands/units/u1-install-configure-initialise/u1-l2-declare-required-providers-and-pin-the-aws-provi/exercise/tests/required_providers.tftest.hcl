mock_provider "aws" {}

run "terraform_required_version_constraint_is_set" {
  command = apply

  assert {
    condition     = output.required_terraform_version == ">= 1.1.0"
    error_message = "required_version in terraform.tf should be \">= 1.1.0\", but the output does not match. Check that you set required_version = \">= 1.1.0\" inside the terraform {} block in terraform.tf and that local.required_terraform_version in main.tf matches it."
  }
}

run "aws_provider_version_constraint_is_set" {
  command = apply

  assert {
    condition     = output.required_aws_constraint == "~> 6.0"
    error_message = "The AWS provider version constraint should be \"~> 6.0\", but the output does not match. Check that you set version = \"~> 6.0\" inside the required_providers block in terraform.tf and that local.required_aws_constraint in main.tf matches it."
  }
}

run "aws_provider_source_uses_hashicorp_namespace" {
  command = apply

  assert {
    condition     = output.required_aws_constraint != ""
    error_message = "The required_aws_constraint output is empty. Make sure the required_providers block in terraform.tf has source = \"hashicorp/aws\" and version = \"~> 6.0\"."
  }
}
