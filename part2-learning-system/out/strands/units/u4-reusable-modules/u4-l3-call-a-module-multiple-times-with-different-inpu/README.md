# Call a module multiple times with different inputs

*Reusable Modules*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the solution does not pass its own checks: tests/for_each_module.tftest.hcl... in progress run "two_storage_instances_exist"... pass run "storage_instances_have_distinct_bucket_names"... pass run "outputs_reference_correct_instances"... fail tests/for_each_module.tftest.hcl... tearing down...

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Call the same child module twice from the root module with different input values and verify both instances are planned as distinct resources
- Use for_each on a module block to create multiple module instances from a single block, referencing each.key to pass distinct values

## Where we are

Earlier lessons introduced child modules with input variables and outputs, and showed how a root module calls a single child module by name. The previous lesson added a storage module that creates an S3 bucket, wired into the root module alongside the network and compute modules.

## The idea

## Calling the same module more than once

The root module can be configured to call child modules multiple times within the same configuration ([source](https://developer.hashicorp.com/terraform/language/modules)). The simplest way is to write two separate module blocks that both point at the same source path but give each block a different name and different input values ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). Terraform treats them as completely independent sets of resources.

```hcl
module "storage_assets" {
  source      = "./modules/storage"
  bucket_name = "my-project-assets"
}

module "storage_logs" {
  source      = "./modules/storage"
  bucket_name = "my-project-logs"
}
```

This works, but it means adding a new block every time you need another instance.

## Using for_each on a module block

`for_each` can be used on both resource blocks and module blocks ([source](https://developer.hashicorp.com/terraform/tutorials/configuration-language/for-each)). When applied to a module block, it loops through a set of keys so that Terraform provisions similar but distinct module instances ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). The source and input variables are declared once, and `each.key` supplies the per-instance value ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)).

```hcl
module "bucket" {
  for_each = toset(["assets", "media"])
  source   = "./publish_bucket"
  name     = "${each.key}_bucket"
}
```

You can differentiate between instances created with `for_each` by indexing them with the map key, for example `module.bucket["assets"].bucket_id` ([source](https://developer.hashicorp.com/terraform/tutorials/configuration-language/for-each)). A `for_each` module block with a local path source and input variables can create multiple distinct instances of a child module from the root module ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)).

## Worked example

**Goal:** The storage module at `./modules/storage` accepts a `bucket_name` variable. Create two S3 buckets — one for assets, one for logs — first using two module blocks, then collapse them into a single `for_each` block.

---

### Step 1 — Two explicit module blocks

```hcl
# root main.tf
module "storage_assets" {
  source      = "./modules/storage"
  bucket_name = "my-project-assets"
}

module "storage_logs" {
  source      = "./modules/storage"
  bucket_name = "my-project-logs"
}
```

The root module calls the same child module twice with different names and different input values ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). Running `terraform plan` shows two resources: `module.storage_assets.aws_s3_bucket.main` and `module.storage_logs.aws_s3_bucket.main`. They are entirely independent — Terraform tracks them under different addresses.

---

### Step 2 — Collapse into a single for_each block

```hcl
# root main.tf
module "storage" {
  for_each = toset(["my-project-assets", "my-project-logs"])

  source      = "./modules/storage"
  bucket_name = each.key
}
```

`for_each` loops through a set of keys so that Terraform provisions similar but distinct module instances ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). `toset()` is used here because `for_each` on a module block requires a set or map, and the function converts the list literal into a set ([source](https://developer.hashicorp.com/terraform/language/block/resource)).

`each.key` is used to pass a distinct `bucket_name` to each instance ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)). Running `terraform plan` again shows the same two bucket resources — now addressed as `module.storage["my-project-assets"].aws_s3_bucket.main` and `module.storage["my-project-logs"].aws_s3_bucket.main`.

---

### Step 3 — Reference a specific instance

If an output needed one bucket's ID:

```hcl
output "assets_bucket_id" {
  value = module.storage["my-project-assets"].bucket_id
}
```

Indexing with the map key differentiates the instances ([source](https://developer.hashicorp.com/terraform/tutorials/configuration-language/for-each)).

## Your turn

You are extending the project from the previous lesson. A `storage` module already exists at `./modules/storage`; it takes a `bucket_name` input and exposes a `bucket_id` output.

**Part A:** In `main.tf`, add a second module block (alongside the existing one) that calls `./modules/storage` again with `bucket_name = "my-project-logs"`. The existing block uses `bucket_name = "my-project-assets"`.

**Part B:** Replace both storage module blocks with a single module block named `storage` that uses `for_each` over a set containing both names (`"my-project-assets"` and `"my-project-logs"`), passing `each.key` as `bucket_name`.

Update `outputs.tf` to expose the `bucket_id` from each instance of the `for_each` module, using the keys `"my-project-assets"` and `"my-project-logs"`.

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
