# Lesson u1-l1 — verify your Terraform installation
#
# Run:  terraform -version
# It will print something like:  Terraform v1.16.4
#
# Copy that full string (including the leading "Terraform v") into the
# local value below, then run:  terraform test

locals {
  # TODO: replace the empty string with the version string reported by
  #       `terraform -version` on your machine, e.g. "Terraform v1.16.4"
  installed_version = ""
}

output "installed_version" {
  value       = local.installed_version
  description = "The version string reported by terraform -version on this machine."
}
