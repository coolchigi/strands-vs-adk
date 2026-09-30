mock_provider "aws" {}

run "verify_dev_configuration" {
  command = apply

  variables {
    environment = "dev"
    extra_tags = {
      CostCenter = "1234"
    }
  }

  assert {
    condition     = aws_instance.web.instance_type == "t3.micro"
    error_message = "Instance type should be looked up as t3.micro for the dev environment."
  }

  assert {
    condition     = aws_instance.web.user_data == "#!/bin/bash\necho \"Hello from dev-server\"\n"
    error_message = "user_data must match '#!/bin/bash\necho \"Hello from dev-server\"\n'."
  }

  assert {
    condition     = aws_instance.web.tags["Name"] == "dev-web" && aws_instance.web.tags["Environment"] == "dev" && aws_instance.web.tags["CostCenter"] == "1234"
    error_message = "Tags must contain Name = 'dev-web', Environment = 'dev', and merged CostCenter = '1234'."
  }
}

run "verify_prod_configuration" {
  command = apply

  variables {
    environment = "prod"
  }

  assert {
    condition     = aws_instance.web.instance_type == "t3.large"
    error_message = "Instance type should be looked up as t3.large for the prod environment."
  }

  assert {
    condition     = aws_instance.web.user_data == "#!/bin/bash\necho \"Hello from prod-server\"\n"
    error_message = "user_data must match '#!/bin/bash\necho \"Hello from prod-server\"\n'."
  }
}
