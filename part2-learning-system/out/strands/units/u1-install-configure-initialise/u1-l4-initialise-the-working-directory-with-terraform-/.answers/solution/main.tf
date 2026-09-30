locals {
  lock_provider_source = "registry.terraform.io/hashicorp/aws"
  provider_install_dir = "registry.terraform.io/hashicorp/aws"
}

output "lock_provider_source" {
  value       = local.lock_provider_source
  description = "The provider source address recorded in .terraform.lock.hcl."
}

output "provider_install_dir" {
  value       = local.provider_install_dir
  description = "The path prefix inside .terraform/providers/ for the AWS provider."
}
