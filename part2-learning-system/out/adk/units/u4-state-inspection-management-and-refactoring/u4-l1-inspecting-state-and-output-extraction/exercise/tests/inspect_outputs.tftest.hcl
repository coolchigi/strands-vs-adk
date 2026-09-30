mock_provider "aws" {}

run "verify_outputs" {
  command = apply

  assert {
    condition     = output.vpc_cidr == "10.0.0.0/16"
    error_message = "The vpc_cidr output must expose module.vpc.vpc_cidr."
  }

  assert {
    condition     = output.api_token == "supersecrettoken123"
    error_message = "The api_token output must expose var.api_token with sensitive = true."
  }
}
