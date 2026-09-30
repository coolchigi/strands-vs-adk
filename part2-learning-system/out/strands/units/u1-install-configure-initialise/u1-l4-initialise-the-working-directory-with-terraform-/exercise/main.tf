locals {
  # TODO: Set this to the provider block label you see in .terraform.lock.hcl
  #       (the fully-qualified source address, e.g. "registry.terraform.io/hashicorp/aws").
  lock_provider_source = ""

  # TODO: Set this to the path prefix you find inside .terraform/providers/
  #       that identifies the provider (the same three-segment address).
  provider_install_dir = ""
}

output "lock_provider_source" {
  value       = local.lock_provider_source
  description = "The provider source address recorded in .terraform.lock.hcl."
}

output "provider_install_dir" {
  value       = local.provider_install_dir
  description = "The path prefix inside .terraform/providers/ for the AWS provider."
}
