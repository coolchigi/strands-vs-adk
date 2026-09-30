# Reusable Modules

## Outcomes

- Structure a Terraform project as a root module that calls local child modules
- Write a child module with variables.tf, main.tf, and outputs.tf so it is fully self-contained
- Thread outputs from one module into the inputs of another to express cross-module dependencies
- Call the same child module multiple times from the root module with different inputs

## Lessons

- [Structure a project as root and child modules](u4-l1-structure-a-project-as-root-and-child-modules/README.md)
- [Write child module inputs and outputs](u4-l2-write-child-module-inputs-and-outputs/README.md)
- [Call a module multiple times with different inputs](u4-l3-call-a-module-multiple-times-with-different-inpu/README.md)

## Project

Refactor the Unit 2/3 configuration into three child modules under a modules/ directory: modules/storage (S3 bucket), modules/compute (EC2 instance), and modules/network (subnets). Each module must have variables.tf, main.tf, and outputs.tf. The root module's main.tf calls all three, threading the subnet IDs from the network module into the compute module. Run terraform init, plan, and apply against LocalStack and verify all resources are created. Then call the storage module a second time with a different bucket name.
