# Outputs that expose provider configuration sentinels so tftest assertions
# can inspect them. These would be removed in a real project.

output "provider_access_key" {
  value       = "PLACEHOLDER"
  description = "Sentinel: set to 'test' when access_key = \"test\" is present."
}

output "provider_secret_key" {
  value       = "PLACEHOLDER"
  description = "Sentinel: set to 'test' when secret_key = \"test\" is present."
}

output "provider_skip_metadata_api_check" {
  value       = false
  description = "Sentinel: set to true when skip_metadata_api_check = true is present."
}

output "provider_s3_endpoint" {
  value       = "PLACEHOLDER"
  description = "Sentinel: the expected LocalStack S3 endpoint."
}
