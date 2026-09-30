mock_provider "aws" {}

run "verify_outputs" {
  command = apply

  assert {
    condition     = output.vpc_id == aws_vpc.main.id
    error_message = "The vpc_id output must reference aws_vpc.main.id."
  }

  assert {
    condition     = output.public_subnet_ids == [aws_subnet.public.id]
    error_message = "The public_subnet_ids output must equal [aws_subnet.public.id] using splat syntax."
  }

  assert {
    condition     = output.db_token == "supersecret-token-123"
    error_message = "The db_token output value must equal 'supersecret-token-123'."
  }

  assert {
    condition     = issensitive(output.db_token)
    error_message = "The db_token output must have sensitive set to true."
  }
}