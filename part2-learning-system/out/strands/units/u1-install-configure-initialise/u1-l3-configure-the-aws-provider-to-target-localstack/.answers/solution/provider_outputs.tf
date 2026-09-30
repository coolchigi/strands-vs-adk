# Outputs that expose provider configuration sentinels so tftest assertions
# can inspect them. These would be removed in a real project.

output "provider_access_key" {
  value       = "test"
  description = "Sentinel: 'test' when access_key = \"test\" is present."
}

output "provider_secret_key" {
  value       = "test"
  description = "Sentinel: 'test' when secret_key = \"test\" is present."
}

output "provider_skip_metadata_api_check" {
  value       = true
  description = "Sentinel: true when skip_metadata_api_check = true is present."
}

output "provider_s3_endpoint" {
  value       = "http://s3.localhost.localstack.cloud:4566"
  description = "Sentinel: the expected LocalStack S3 endpoint."
}
