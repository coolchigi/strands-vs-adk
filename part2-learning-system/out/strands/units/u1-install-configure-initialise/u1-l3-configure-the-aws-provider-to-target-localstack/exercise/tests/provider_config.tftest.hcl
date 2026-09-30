mock_provider "aws" {}

run "provider_has_mock_access_key" {
  command = apply

  assert {
    condition     = output.provider_access_key == "test"
    error_message = "provider.tf: access_key must be set to \"test\" and provider_outputs.tf must reflect that value."
  }
}

run "provider_has_mock_secret_key" {
  command = apply

  assert {
    condition     = output.provider_secret_key == "test"
    error_message = "provider.tf: secret_key must be set to \"test\" and provider_outputs.tf must reflect that value."
  }
}

run "provider_skips_metadata_api_check" {
  command = apply

  assert {
    condition     = output.provider_skip_metadata_api_check == true
    error_message = "provider.tf: skip_metadata_api_check must be set to true and provider_outputs.tf must reflect that value."
  }
}

run "provider_s3_endpoint_is_localstack" {
  command = apply

  assert {
    condition     = output.provider_s3_endpoint == "http://s3.localhost.localstack.cloud:4566"
    error_message = "provider.tf: the s3 entry in the endpoints block must be \"http://s3.localhost.localstack.cloud:4566\" and provider_outputs.tf must reflect that value."
  }
}
