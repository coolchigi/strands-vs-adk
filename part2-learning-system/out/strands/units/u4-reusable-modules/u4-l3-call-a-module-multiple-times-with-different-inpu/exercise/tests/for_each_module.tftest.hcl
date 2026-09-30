mock_provider "aws" {}

run "two_storage_instances_exist" {
  command = apply

  assert {
    condition     = module.storage["my-project-assets"].bucket_id != ""
    error_message = "Expected a storage module instance keyed 'my-project-assets' but it was not found. Make sure your for_each set includes 'my-project-assets' and you are using each.key as bucket_name."
  }

  assert {
    condition     = module.storage["my-project-logs"].bucket_id != ""
    error_message = "Expected a storage module instance keyed 'my-project-logs' but it was not found. Make sure your for_each set includes 'my-project-logs' and you are using each.key as bucket_name."
  }
}

run "storage_instances_have_distinct_bucket_names" {
  command = apply

  assert {
    condition     = module.storage["my-project-assets"].bucket_id != module.storage["my-project-logs"].bucket_id
    error_message = "The two storage instances must produce distinct bucket IDs. Check that each.key is passed as bucket_name so each instance gets a different name."
  }
}

run "outputs_reference_correct_instances" {
  command = apply

  assert {
    condition     = output.assets_bucket_id.value == module.storage["my-project-assets"].bucket_id
    error_message = "The 'assets_bucket_id' output should reference module.storage[\"my-project-assets\"].bucket_id."
  }

  assert {
    condition     = output.logs_bucket_id.value == module.storage["my-project-logs"].bucket_id
    error_message = "The 'logs_bucket_id' output should reference module.storage[\"my-project-logs\"].bucket_id."
  }
}
