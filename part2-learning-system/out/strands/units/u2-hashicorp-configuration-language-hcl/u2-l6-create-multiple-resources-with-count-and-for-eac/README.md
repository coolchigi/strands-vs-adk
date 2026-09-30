# Create multiple resources with count and for_each

*HashiCorp Configuration Language (HCL)*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - u2-l6: 'Choose between count and for_each for a given scenario, justifying the decision' asks the learner to evaluate, and a quiz can't show that. It needs an exercise.
> - u2-l6 teaches from claims we don't have: ['24c0b2e968051']
> - the checks don't test the gap at main.tf line 43: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Use count with length() to create one subnet per availability zone and reference individual instances with index notation
- Rewrite a count-based resource block using for_each with a map, referencing each.key and each.value inside the block
- Choose between count and for_each for a given scenario, justifying the decision

## Where we are

Earlier lessons introduced variables, locals, and outputs, and built a VPC with a single `aws_subnet` block. You also saw how `cidrsubnet()` carves a VPC CIDR into smaller blocks. This lesson uses those primitives to stamp out multiple resources automatically.

## The idea

## count: one resource per list element

The `count` meta-argument tells Terraform how many instances of a resource to create. ([source](https://developer.hashicorp.com/terraform/language/block/resource)) Passing `length(var.availability_zones)` as the value creates exactly one instance per element in the list. ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/count)) Inside the block, `count.index` is the zero-based index of the current instance, starting at 0. ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/count))

```hcl
resource "aws_subnet" "public" {
  count      = length(var.availability_zones)
  vpc_id     = aws_vpc.main.id
  cidr_block = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]
}
```

After apply, the resource reference becomes a **list of objects**. ([source](https://developer.hashicorp.com/terraform/language/expressions/references)) A splat expression retrieves all IDs at once: `aws_subnet.public[*].id`. ([source](https://developer.hashicorp.com/terraform/language/expressions/references)) A single instance is accessed by index: `aws_subnet.public[0].id`. ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/count))

One important constraint: the `count` value must be known at plan time and cannot refer to attributes that are only computed after apply. ([source](https://developer.hashicorp.com/terraform/language/expressions/references))

## for_each: one resource per map entry

`for_each` accepts a map of key-value pairs or a set of strings. ([source](https://developer.hashicorp.com/terraform/language/block/resource)) Inside the block, `each.key` holds the map key and `each.value` holds the corresponding value. ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each))

```hcl
resource "aws_s3_bucket" "env" {
  for_each = tomap({
    logs    = "us-east-1"
    backups = "us-west-2"
  })
  bucket = each.key
}
```

After apply, the resource reference becomes a **map of objects** keyed by the map keys. ([source](https://developer.hashicorp.com/terraform/language/expressions/references)) A specific instance is reached with `aws_s3_bucket.env["logs"].id`. ([source](https://developer.hashicorp.com/terraform/language/expressions/references)) Because `for_each` resources are maps rather than lists, splat expressions do not work on them directly; use `values(aws_s3_bucket.env)[*].id` instead. ([source](https://developer.hashicorp.com/terraform/language/expressions/references))

Like `count`, all values iterated by `for_each` must be known before Terraform contacts any remote API. ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)) Sensitive values cannot be used as `for_each` arguments because Terraform always discloses them in UI output to identify instances. ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each)) You cannot use both `count` and `for_each` in the same block. ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/count))

## Choosing between count and for_each

Use `count` when you want nearly identical instances and an integer index is sufficient to differentiate them. ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/count)) Use `for_each` when each instance has distinct configuration values that are naturally expressed as named keys in a map, rather than integer offsets. ([source](https://developer.hashicorp.com/terraform/language/meta-arguments/for_each))

A practical rule: if removing one instance from the middle of a `count`-based list would renumber every subsequent instance (and therefore plan to destroy and recreate them), that is a signal to switch to `for_each` with stable string keys instead.

## Worked example

**Goal:** Create two subnets (one per AZ) with `count`, then add two S3 buckets with `for_each`.

**Step 1 – Replace the single subnet with a count-based block.**

The variable `var.availability_zones` is `["us-east-1a", "us-east-1b"]`. We want one subnet per AZ.

```hcl
resource "aws_subnet" "public" {
  count             = length(var.availability_zones)   # 2 instances
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]

  tags = {
    Name    = "public-${count.index}"
    Project = local.name_prefix
  }
}
```

`count.index` is 0 for the first instance and 1 for the second. `cidrsubnet("10.0.0.0/16", 8, 0)` → `10.0.0.0/24`; `cidrsubnet("10.0.0.0/16", 8, 1)` → `10.0.1.0/24`. Each subnet lands in a distinct AZ.

**Step 2 – Output all subnet IDs with a splat expression.**

```hcl
output "subnet_ids" {
  description = "IDs of all public subnets"
  value       = aws_subnet.public[*].id
}
```

Because `aws_subnet.public` is a list of objects, `[*].id` collects every `.id` into a list. ([source](https://developer.hashicorp.com/terraform/language/expressions/references))

**Step 3 – Add S3 buckets with for_each.**

```hcl
resource "aws_s3_bucket" "named" {
  for_each = tomap({
    logs    = "access-logs"
    backups = "nightly-backups"
  })

  bucket = each.key   # "logs" or "backups"

  tags = {
    Purpose = each.value   # "access-logs" or "nightly-backups"
    Project = local.name_prefix
  }
}
```

Terraform creates `aws_s3_bucket.named["logs"]` and `aws_s3_bucket.named["backups"]` as separate, independently-addressable objects. ([source](https://developer.hashicorp.com/terraform/language/expressions/references))

**Step 4 – Run `terraform plan`.**

The plan output shows:
```
# aws_subnet.public[0] will be created
# aws_subnet.public[1] will be created
# aws_s3_bucket.named["backups"] will be created
# aws_s3_bucket.named["logs"] will be created
```

Two subnets (indexed 0 and 1) and two buckets (keyed by name) — exactly what we expect.

## Your turn

Starting from the provided files:
1. Replace the single `aws_subnet.public` block with one that uses `count = length(var.availability_zones)`. Assign each subnet a unique CIDR using `cidrsubnet(var.vpc_cidr, 8, count.index)` and place it in `var.availability_zones[count.index]`.
2. Replace the existing `subnet_id` output with a `subnet_ids` output (plural) that returns all subnet IDs as a list using a splat expression.
3. Replace the single `aws_s3_bucket.assets` block with a `for_each`-based resource called `aws_s3_bucket.env` that iterates over a map with two entries — key `"logs"` with value `"access-logs"` and key `"backups"` with value `"nightly-backups"` — setting `bucket = each.key` and a tag `Purpose = each.value`.
4. Replace the `bucket_id` output with a `bucket_ids` output that collects all bucket IDs from the `for_each` resource using a for expression: `[for b in aws_s3_bucket.env : b.id]`.
5. Run `terraform test` to verify.

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
