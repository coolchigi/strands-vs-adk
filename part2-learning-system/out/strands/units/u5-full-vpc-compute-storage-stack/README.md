# Full VPC, Compute & Storage Stack

## Outcomes

- Write a networking module that creates a VPC, subnets, internet gateway, and route tables using cidrsubnet
- Write a compute module that places EC2 instances inside subnets received from the networking module
- Write a storage module that provisions S3 buckets and optionally EBS volumes
- Compose all three modules in a root module, threading outputs across modules to express dependencies
- Apply the full stack to LocalStack, verify every resource with the AWS CLI, and destroy it cleanly

## Lessons

- [Write the networking module](u5-l1-write-the-networking-module/README.md)
- [Write the compute module](u5-l2-write-the-compute-module/README.md)
- [Write the storage module](u5-l3-write-the-storage-module/README.md)
- [Compose all three modules and verify the full stack](u5-l4-compose-all-three-modules-and-verify-the-full-st/README.md)

## Project

This unit's project IS the capstone: apply the complete root module (networking + compute + storage) to LocalStack, then verify every created resource using AWS CLI commands (describe-vpcs, describe-instances, s3 ls), inspect two resources with terraform state show, and finally run terraform destroy and confirm an empty state file. The project is complete when: all three modules apply without error, CLI verification shows the correct VPC CIDR and instance placement, and the state file is empty after destroy.
