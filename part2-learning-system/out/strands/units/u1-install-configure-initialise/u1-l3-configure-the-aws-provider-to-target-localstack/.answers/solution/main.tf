# Lesson u1-l1 — verify your Terraform installation

locals {
  installed_version = "Terraform v1.16.4"

  # These values mirror what you write in terraform.tf so the checks
  # can verify the constraints without needing a real provider.
  required_terraform_version = ">= 1.1.0"
  required_aws_constraint    = "~> 6.0"
}

output "installed_version" {
  value       = local.installed_version
  description = "The version string reported by terraform -version on this machine."
}

output "required_terraform_version" {
  value       = local.required_terraform_version
  description = "The required_version constraint used in terraform.tf."
}

output "required_aws_constraint" {
  value       = local.required_aws_constraint
  description = "The AWS provider version constraint used in required_providers."
}
