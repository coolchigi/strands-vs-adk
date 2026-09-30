mock_provider "aws" {}

run "child_module_called_and_outputs_exposed" {
  command = apply

  assert {
    condition     = module.logs.bucket_id != ""
    error_message = "module.logs does not exist or its bucket_id output is empty. Make sure you have a module block named 'logs' sourcing ./modules/storage with bucket_name set, and that modules/storage/outputs.tf exposes bucket_id."
  }

  assert {
    condition     = module.backups.bucket_id != ""
    error_message = "module.backups does not exist or its bucket_id output is empty. Make sure you have a module block named 'backups' sourcing ./modules/storage with bucket_name set, and that modules/storage/outputs.tf exposes bucket_id."
  }

  assert {
    condition     = output.logs_bucket_id != ""
    error_message = "Root output 'logs_bucket_id' is missing or empty. Add an output in the root outputs.tf that reads module.logs.bucket_id."
  }

  assert {
    condition     = output.backups_bucket_id != ""
    error_message = "Root output 'backups_bucket_id' is missing or empty. Add an output in the root outputs.tf that reads module.backups.bucket_id."
  }

  assert {
    condition     = module.logs.bucket_id != module.backups.bucket_id
    error_message = "The logs and backups modules returned the same bucket_id. Make sure each module block passes a different bucket_name."
  }
}
