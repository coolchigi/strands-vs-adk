# Modular Infrastructure Architecture

## Outcomes

- Structure Terraform code into standard root and child module hierarchies
- Call modules from local file paths and external VCS/registry sources
- Wire module inputs and outputs together to form end-to-end multi-tier architectures

## Lessons

- [Standard Module Architecture and Hierarchy](u3-l1-standard-module-architecture-and-hierarchy/README.md)
- [Calling Modules from Local and External Sources](u3-l2-calling-modules-from-local-and-external-sources/README.md)
- [Inter-Module Data Flow and Multi-Instance Scaling](u3-l3-inter-module-data-flow-and-multi-instance-scalin/README.md)

## Project

Design a complete modular AWS infrastructure repository consisting of a root module and three child modules in `modules/`: `vpc` (network and subnets), `compute` (EC2 instance and security group), and `storage` (S3 bucket with versioning). Wire the outputs of `vpc` as inputs to `compute`. Initialize and apply the entire multi-module stack against LocalStack to verify that all resources are created and wired together in state without incurring any cloud costs.
