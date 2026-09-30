# Standard Module Architecture and Hierarchy

*Modular Infrastructure Architecture*

## By the end of this lesson you can

- Organize infrastructure configurations into root modules and child modules located in modules/ directories
- Explain how provider inheritance functions between parent and child modules, including configuration_aliases

## Where we are

In earlier lessons, we defined all infrastructure components—such as VPCs, subnets, route tables, and EC2 instances—directly within the workspace configuration files. We also established input variables to parameterize settings and output values to expose computed attributes like IDs and ARNs.

## The idea

A module in Terraform represents a collection of resources managed together ([source](https://developer.hashicorp.com/terraform/language/modules)). The configuration files located in the root directory of a workspace are referred to by Terraform as the root module ([source](https://developer.hashicorp.com/terraform/language/modules)). The root module is the only required element in the standard module structure, requiring Terraform files in the repository's root directory ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). The recommended filenames for a minimal Terraform module are `main.tf`, `variables.tf`, and `outputs.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

Modules declared via module blocks in a configuration are called child modules ([source](https://developer.hashicorp.com/terraform/language/modules)). Nested child modules in the standard module structure should be placed in the `modules/` subdirectory ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). A root module can call the same child module multiple times within a single configuration ([source](https://developer.hashicorp.com/terraform/language/modules)). Child modules called by the root module can themselves call nested child modules ([source](https://developer.hashicorp.com/terraform/language/modules)). In a complex module where resource creation is split across multiple files, any nested module calls should be placed in `main.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

Provider configurations should be defined in the root module, and child modules receive their provider configurations from their parent modules ([source](https://developer.hashicorp.com/terraform/language/block/provider)). Child modules must declare expected provider aliases using the `configuration_aliases` argument in their `required_providers` block ([source](https://developer.hashicorp.com/terraform/language/block/provider)).

## Worked example

Suppose you want to extract S3 bucket creation out of a monolithic configuration into a reusable child module.

First, following the standard module structure, create the directory `modules/s3_storage` and add the minimal recommended files: `main.tf`, `variables.tf`, and `outputs.tf`.

In `modules/s3_storage/variables.tf`, define the input variables the module needs:
```hcl
variable "bucket_name" {
  type        = string
  description = "The name of the S3 bucket"
}
```

In `modules/s3_storage/main.tf`, declare the resource. Notice that we do not declare a `provider "aws"` block here, because the child module inherits its provider configuration from its parent:
```hcl
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
}
```

In `modules/s3_storage/outputs.tf`, export the computed attributes:
```hcl
output "bucket_arn" {
  description = "ARN of the created bucket"
  value       = aws_s3_bucket.this.arn
}
```

Finally, in the root module's `main.tf`, call the child module using a `module` block:
```hcl
module "storage" {
  source      = "./modules/s3_storage"
  bucket_name = "my-app-storage-bucket"
}
```

Any root outputs can now reference `module.storage.bucket_arn`.

## Your turn

Refactor the existing monolithic infrastructure by creating a child module under `modules/vpc` with `main.tf`, `variables.tf`, and `outputs.tf`.
1. In `modules/vpc/main.tf`, declare the VPC, internet gateway, subnets, route table, and route table association resources.
2. In `modules/vpc/outputs.tf`, export `vpc_id` (the ID of `aws_vpc.main`) and `public_subnet_id` (the ID of `aws_subnet.public`).
3. In the root `main.tf`, call the `vpc` child module using `source = "./modules/vpc"`, passing `var.vpc_cidr` and `var.public_subnet_cidr`. Wire `aws_instance.web.subnet_id` to `module.vpc.public_subnet_id`.
4. In the root `outputs.tf`, update `vpc_id` to `module.vpc.vpc_id` and `public_subnet_ids` to `[module.vpc.public_subnet_id]`.

The tests run with `terraform test`, so you'll need [Terraform](https://developer.hashicorp.com/terraform/install) installed.

Your files are in `exercise/`. When you think it works:

```bash
learn check
```

Stuck? `learn hint` gives one hint at a time. `learn solution` shows the answer, and records that you looked.

## Check yourself

3 questions. Answer them before you see the answers:

```bash
learn quiz
```
