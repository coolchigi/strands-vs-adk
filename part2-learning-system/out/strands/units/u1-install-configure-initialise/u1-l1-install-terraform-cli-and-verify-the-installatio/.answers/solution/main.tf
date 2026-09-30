# Lesson u1-l1 — verify your Terraform installation

locals {
  installed_version = "Terraform v1.16.4"
}

output "installed_version" {
  value       = local.installed_version
  description = "The version string reported by terraform -version on this machine."
}
