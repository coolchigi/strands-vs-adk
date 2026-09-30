provider "aws" {
  # TODO: add access_key set to "test"
  # TODO: add secret_key set to "test"
  region = "us-east-1"

  skip_credentials_validation = true
  # TODO: add skip_metadata_api_check set to true

  endpoints {
    # TODO: add s3 endpoint pointing to http://s3.localhost.localstack.cloud:4566
    ec2 = "http://localhost:4566"
  }
}
