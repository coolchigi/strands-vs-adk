mock_provider "aws" {}

run "lock_provider_source_is_set" {
  command = apply

  assert {
    condition     = output.lock_provider_source == "registry.terraform.io/hashicorp/aws"
    error_message = "lock_provider_source should be \"registry.terraform.io/hashicorp/aws\" — open .terraform.lock.hcl and copy the label from the provider block."
  }
}

run "provider_install_dir_is_set" {
  command = apply

  assert {
    condition     = output.provider_install_dir == "registry.terraform.io/hashicorp/aws"
    error_message = "provider_install_dir should be \"registry.terraform.io/hashicorp/aws\" — run 'find .terraform/providers -maxdepth 3 -type d' and copy the three-segment path prefix."
  }
}
