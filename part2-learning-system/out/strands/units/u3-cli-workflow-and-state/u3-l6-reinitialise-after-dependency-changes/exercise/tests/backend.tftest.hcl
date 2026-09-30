mock_provider "aws" {}

run "backend_s3_bucket" {
  command = apply

  assert {
    condition     = output.backend_bucket == "my-company-tf-state"
    error_message = "backend 's3' bucket must be \"my-company-tf-state\""
  }
}

run "backend_s3_key" {
  command = apply

  assert {
    condition     = output.backend_key == "myproject/dev/terraform.tfstate"
    error_message = "backend 's3' key must be \"myproject/dev/terraform.tfstate\""
  }
}

run "backend_s3_region" {
  command = apply

  assert {
    condition     = output.backend_region == "us-east-1"
    error_message = "backend 's3' region must be \"us-east-1\""
  }
}

run "backend_s3_dynamodb" {
  command = apply

  assert {
    condition     = output.backend_dynamodb_table == "my-company-tf-locks"
    error_message = "backend 's3' dynamodb_table must be \"my-company-tf-locks\""
  }
}

run "backend_s3_encrypt" {
  command = apply

  assert {
    condition     = output.backend_encrypt == true
    error_message = "backend 's3' encrypt must be true"
  }
}
