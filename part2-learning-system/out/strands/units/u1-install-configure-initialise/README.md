# Install, Configure & Initialise

## Outcomes

- Install the Terraform CLI and verify it runs
- Write a terraform block that pins the AWS provider version
- Configure the AWS provider to target LocalStack so no real AWS calls are made
- Run terraform init successfully and understand what it produces

## Lessons

- [Install Terraform CLI and verify the installation](u1-l1-install-terraform-cli-and-verify-the-installatio/README.md)
- [Declare required_providers and pin the AWS provider version](u1-l2-declare-required-providers-and-pin-the-aws-provi/README.md)
- [Configure the AWS provider to target LocalStack](u1-l3-configure-the-aws-provider-to-target-localstack/README.md)
- [Initialise the working directory with terraform init](u1-l4-initialise-the-working-directory-with-terraform-/README.md)

## Project

Starting from an empty directory, create a complete Terraform configuration (terraform.tf + main.tf) that targets LocalStack, pins the hashicorp/aws provider to ~> 5.0, and initialises cleanly. Verify with terraform -version and terraform init; confirm the .terraform directory and .terraform.lock.hcl exist and contain the expected provider version. No resources need to be declared yet.
