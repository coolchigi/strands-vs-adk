# Checks that the learner filled in a plausible Terraform version string.
# Any string matching "Terraform v<major>.<minor>.<patch>" passes,
# so every valid installation is accepted.

run "version_string_is_set" {
  command = apply

  assert {
    condition     = output.installed_version != ""
    error_message = "installed_version is still empty. Copy the string printed by `terraform -version` into the local value in main.tf."
  }

  assert {
    condition     = can(regex("^Terraform v[0-9]+\\.[0-9]+\\.[0-9]+", output.installed_version))
    error_message = "installed_version doesn't look like a Terraform version string. It should start with 'Terraform v' followed by three numbers, e.g. 'Terraform v1.16.4'."
  }
}
