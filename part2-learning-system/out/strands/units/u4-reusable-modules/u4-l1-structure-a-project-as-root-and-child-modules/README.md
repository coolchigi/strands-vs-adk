# Structure a project as root and child modules

*Reusable Modules*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - Quiz question 3, option D reads "Any file works equally well; the three standard filenames have no special meaning to Terraform." The lesson's own quiz explanation concedes "Terraform itself does not enforce the convention," and the explanation text nowhere claims Terraform enforces the filenames —...

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Create a modules/ subdirectory with a child module containing variables.tf, main.tf, and outputs.tf, and call it from the root module using a module block with a local source path
- Explain the role of main.tf, variables.tf, and outputs.tf in the standard module structure

## Where we are

Earlier lessons built a working root configuration with S3 buckets, an EC2 instance, a VPC, and subnets — all defined directly in the root module. The configuration uses the AWS provider pinned to `~> 6.0` and stores state in an S3 backend with DynamoDB locking.

## The idea

## What is a module?

A module is a container for multiple resources that are used together ([source](https://developer.hashicorp.com/terraform/language/modules/develop)). The `.tf` files in your working directory when you run `terraform plan` or `terraform apply` together form the **root module** ([source](https://developer.hashicorp.com/terraform/language/modules/develop)). Every Terraform workspace has configuration files in its root directory, which Terraform calls the root module ([source](https://developer.hashicorp.com/terraform/language/modules)).

## The standard module structure

The only required element of the standard module structure is the root module — Terraform files must exist in the root directory ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). Everything else is optional ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). The recommended filenames for a minimal module are `main.tf`, `variables.tf`, and `outputs.tf`, even if they are empty ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

- **`main.tf`** should be the primary entrypoint of a module; for a simple module this is where all resources are created ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).
- **`variables.tf`** contains the input variable declarations ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).
- **`outputs.tf`** contains the output value declarations ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

All variables and outputs should have one or two sentence descriptions explaining their purpose ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

## Child modules and the modules/ subdirectory

To define a child module, create a new directory for it and place one or more `.tf` files inside, just as you would for a root module ([source](https://developer.hashicorp.com/terraform/language/modules/develop)). Nested child modules should be stored under the `modules/` subdirectory of the root module ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). A complete module structure places nested modules under `modules/` — each with their own `variables.tf`, `main.tf`, and `outputs.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

## Calling a child module with a module block

Modules configured using `module` blocks are called **child modules**; when a configuration is applied, the root module calls the child module ([source](https://developer.hashicorp.com/terraform/language/modules)). A `module` block requires a `source` attribute that tells Terraform where to find the child module's configuration files ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). When the root module calls nested modules, it should use relative paths such as `./modules/storage` so Terraform treats them as part of the same repository ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). Terraform treats any local directory referenced in the `source` argument of a `module` block as a module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

When Terraform adds a child module's resources to the workspace it manages them as part of the configuration ([source](https://developer.hashicorp.com/terraform/language/modules)). After adding or changing a module block's `source` in the root module, `terraform init` must be run to register the module ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). For local modules, Terraform creates a symlink rather than copying files, so changes take effect immediately without re-running `terraform init` ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)).

## Worked example

### Goal: extract an S3 bucket into a child module

**Step 1 — Create the module directory**

```
modules/
└── storage/
    ├── variables.tf
    ├── main.tf
    └── outputs.tf
```

Nested modules live under `modules/` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). Each gets its own three standard files ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

---

**Step 2 — Declare the input variable (`modules/storage/variables.tf`)**

```hcl
variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket to create."
}
```

Input variable declarations belong in `variables.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). The description explains the variable's purpose in one sentence ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

---

**Step 3 — Define the resource (`modules/storage/main.tf`)**

```hcl
resource "aws_s3_bucket" "this" {
  bucket = var.bucket_name
}
```

`main.tf` is the primary entrypoint where resources are created ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). The module accepts `bucket_name` through the variable just declared.

---

**Step 4 — Expose an output (`modules/storage/outputs.tf`)**

```hcl
output "bucket_id" {
  description = "The ID of the S3 bucket created by this module."
  value       = aws_s3_bucket.this.id
}
```

Output value declarations belong in `outputs.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). The description is a single sentence as recommended ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

---

**Step 5 — Call the module from the root `main.tf`**

```hcl
module "storage" {
  source      = "./modules/storage"
  bucket_name = "my-app-assets"
}
```

The `source` argument uses a relative path so Terraform treats it as part of the same repository ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). Terraform treats any local directory referenced this way as a module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

---

**Step 6 — Run `terraform init`**

```
$ terraform init
```

After adding a module block's `source`, `terraform init` must be run to register the module ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). For local modules Terraform creates a symlink, so future edits to the module files take effect without re-running `init` ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)).

---

**Step 7 — Verify with `terraform plan`**

```
# module.storage.aws_s3_bucket.this will be created
+ resource "aws_s3_bucket" "this" {
    + bucket = "my-app-assets"
    ...
}
```

The plan shows `module.storage.aws_s3_bucket.this`, confirming the resource belongs to the child module. The root module called the child module and Terraform added its resources to the workspace ([source](https://developer.hashicorp.com/terraform/language/modules)).

## Your turn

Create a child module at `modules/storage/` with three files:
- `variables.tf`: declare a `bucket_name` variable (string, with a description).
- `main.tf`: define an `aws_s3_bucket` resource named `this` that uses `var.bucket_name` as the bucket name.
- `outputs.tf`: expose the bucket's `id` as an output named `bucket_id` (with a description).

In the root `main.tf`, replace the existing `aws_s3_bucket.env` `for_each` resource with **two** `module` blocks — one named `logs` and one named `backups` — each sourcing `./modules/storage` and passing a distinct `bucket_name`. Remove the old `bucket_ids` output from root `outputs.tf` and replace it with two outputs: `logs_bucket_id` and `backups_bucket_id`, reading from the respective module outputs.

Then run:
```
terraform init
terraform test
```

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
