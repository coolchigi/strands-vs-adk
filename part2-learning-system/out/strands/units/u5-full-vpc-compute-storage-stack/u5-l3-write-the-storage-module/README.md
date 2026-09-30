# Write the storage module

*Full VPC, Compute & Storage Stack*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the starter is not valid Terraform, so the learner would see a syntax error instead of a failing test: Error: Unsupported argument on main.tf line 19, in module "storage": 19: bucket_name = each.key An argument named "bucket_name" is not expected here.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Write a storage module that provisions an S3 bucket (and optionally an EBS volume), accepting bucket_name and tags as inputs and exposing bucket ARN, id, and domain as outputs

## Where we are

Earlier lessons built the networking and compute child modules, each organised into variables.tf, main.tf, and outputs.tf under modules/. The root main.tf calls all three module blocks and the root outputs.tf surfaces their values. This lesson adds the storage module alongside them.

## The idea

## Module file layout

The recommended filenames for a minimal module are `main.tf`, `variables.tf`, and `outputs.tf`, even if some start empty ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). Input variable declarations belong in `variables.tf` and output value declarations belong in `outputs.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). A local submodule lives inside a `modules/` subdirectory of the root configuration; the directory name becomes the module name ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

## Declaring variables

`variables.tf` holds variable definitions; any variable without a default value becomes a required argument when the module is called ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). `bucket_name` has no default, so it is required every time the module is used ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). The `tags` variable uses `type = map(string)` and `default = {}`, making it optional ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). All variables should have one or two sentence descriptions explaining their purpose ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

## Writing the resource

A minimal S3 bucket resource block requires only the bucket name as an argument ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)). The storage module's `main.tf` passes `var.bucket_name` and `var.tags` into the bucket resource, wiring the caller's values into the child module resource ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). Provider blocks must not be included inside modules — Terraform inherits the provider from the enclosing configuration automatically ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

## Exposing outputs

Outputs are the only supported way for users to get information about resources configured inside a module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). `outputs.tf` holds those definitions; module outputs are made available to the calling configuration and are often used to pass information to other parts of the configuration ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). The storage module exposes the bucket ARN, name (id), and domain as outputs so the root module and other modules can consume them ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

## Adding a precondition

A `precondition` block inside an output enforces guarantees about resources and returns a custom `error_message` if its condition is false ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)). Placing one on the `bucket_id` output that checks `var.bucket_name != ""` catches an empty name before any resource is created.

## Worked example

### Goal
Add `modules/storage/` with the three standard files, wiring `bucket_name` and `tags` into an `aws_s3_bucket` and surfacing ARN, id, and domain as outputs.

---

#### Step 1 — `modules/storage/variables.tf`

Two variables are needed. `bucket_name` is required (no default); `tags` is optional with an empty-map default.

```hcl
variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket to create."
}

variable "tags" {
  type        = map(string)
  description = "Tags to set on the bucket."
  default     = {}
}
```

`bucket_name` has no `default`, so callers must always supply it ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). `tags` uses `default = {}` so it is optional ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

---

#### Step 2 — `modules/storage/main.tf`

A minimal bucket needs only the name; tags are passed through directly.

```hcl
resource "aws_s3_bucket" "main" {
  bucket = var.bucket_name
  tags   = var.tags
}
```

`var.bucket_name` and `var.tags` wire the caller's values into the resource ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). No provider block is included — Terraform inherits it from the root ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

---

#### Step 3 — `modules/storage/outputs.tf`

Three outputs expose what callers need, plus a precondition that guards against an empty bucket name.

```hcl
output "bucket_id" {
  description = "Name (id) of the S3 bucket."
  value       = aws_s3_bucket.main.bucket

  precondition {
    condition     = var.bucket_name != ""
    error_message = "bucket_name must not be empty."
  }
}

output "bucket_arn" {
  description = "ARN of the S3 bucket."
  value       = aws_s3_bucket.main.arn
}

output "bucket_domain" {
  description = "Domain name of the S3 bucket."
  value       = aws_s3_bucket.main.bucket_domain_name
}
```

`bucket_id` uses `.bucket` (the known input attribute) so its value is always the name you passed in. The precondition fires before any output is returned if `bucket_name` is empty ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)). The three outputs make ARN, id, and domain available to the root module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

---

#### Step 4 — verify from the root

```
terraform init   # picks up the new module directory
terraform plan   # storage module resources appear alongside networking and compute
```

The plan output will list `module.storage["my-project-assets"].aws_s3_bucket.main` and `module.storage["my-project-logs"].aws_s3_bucket.main` alongside the VPC, subnets, and EC2 instances.

## Your turn

Create the storage module inside modules/storage/. In variables.tf declare bucket_name (required, string) and tags (optional, map(string) defaulting to {}), both with descriptions. In main.tf write an aws_s3_bucket resource that sets bucket = var.bucket_name and tags = var.tags. In outputs.tf expose bucket_id (using aws_s3_bucket.main.bucket), bucket_arn (using aws_s3_bucket.main.arn), and bucket_domain (using aws_s3_bucket.main.bucket_domain_name), all with descriptions. Add a precondition on the bucket_id output that checks var.bucket_name != "" with an appropriate error_message. Run the provided tests with: terraform test

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
