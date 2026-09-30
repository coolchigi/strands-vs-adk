# Terraform Language Basics and Core Lifecycle Workflow

## Outcomes

- Declare provider configurations and AWS resource blocks using canonical HCL syntax
- Establish implicit and explicit resource dependencies through attribute cross-references
- Initialize working directories, validate syntax, and preview execution plans
- Provision and destroy real resources against zero-cost LocalStack mock endpoints to generate state

## Lessons

- [Declaring Providers and AWS Resource Blocks](u1-l1-declaring-providers-and-aws-resource-blocks/README.md)
- [Resource Attribute References and Dependency Management](u1-l2-resource-attribute-references-and-dependency-man/README.md)
- [Working Directory Initialization and Configuration Validation](u1-l3-working-directory-initialization-and-configurati/README.md)
- [Planning, Applying, and Destroying Infrastructure](u1-l4-planning-applying-and-destroying-infrastructure/README.md)

## Project

Build an initial network skeleton in a single configuration file containing an AWS provider with mock LocalStack endpoints, an aws_vpc, an aws_internet_gateway, and two public aws_subnets cross-referencing the VPC ID. Initialize the directory, run validate and fmt, generate a speculative plan to disk, apply the plan against LocalStack to verify that terraform.tfstate is generated, and confirm infrastructure integrity.
