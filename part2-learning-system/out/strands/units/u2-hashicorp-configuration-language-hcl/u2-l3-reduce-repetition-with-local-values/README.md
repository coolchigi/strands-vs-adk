# Reduce repetition with local values

*HashiCorp Configuration Language (HCL)*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - Quiz question 3's answer explanation introduces citation [c:88aaa7742c62] — 'A local value can reference another local value using the local.<NAME> syntax [c:88aaa7742c62]' — but this citation identifier does not appear anywhere else in the lesson and has no corresponding checked claim. The same...
> - Quiz question 1's answer explanation asserts 'locals and variables are both resolved during the same evaluation pass' as a rebuttal to distractor B. No citation in the lesson covers Terraform's evaluation ordering. This claim goes beyond what any cited source in the lesson says, violating the...
> - question 1's explanation names an option by its position ("Option B"), and learn.py numbers options from 1. Name it by what it says.
> - question 3's explanation names an option by its position ("Option B"), and learn.py numbers options from 1. Name it by what it says.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Define a locals block that combines input variables and function calls into reusable named expressions, then reference them with local.<NAME> inside resource arguments
- Explain when to use a local value instead of repeating an expression directly

## Where we are

Earlier lessons introduced input variables (declared with `variable` blocks and referenced with `var.<NAME>`) and resource blocks with arguments like `tags`. You also saw that `terraform.tfvars` supplies values for those variables at run time.

## The idea

## What is a local value?

Local values assign names to expressions so you can use the name multiple times within a module instead of repeating that expression ([source](https://developer.hashicorp.com/terraform/language/values/locals)). A `locals` block can be defined in any module, and any valid Terraform expression can be assigned as its value ([source](https://developer.hashicorp.com/terraform/language/values/locals)).

## What can go inside a locals block?

Within a `locals` block you can reference variables, resource attributes, function outputs, and other local values ([source](https://developer.hashicorp.com/terraform/language/values/locals)). A common pattern is to build a name prefix by combining two input variables with string interpolation ([source](https://developer.hashicorp.com/terraform/language/values/locals)). You can also call built-in functions — for example, `length` can count items in a list right inside the block ([source](https://developer.hashicorp.com/terraform/language/values/locals)). One local can even reference another local using the same `local.<NAME>` syntax, as long as no circular dependency is introduced ([source](https://developer.hashicorp.com/terraform/language/expressions/references)).

## How do you reference a local value?

Use the singular `local.<NAME>` syntax to reference values from a `locals` block — note that the block is named `locals` (plural) but references use `local` (singular) ([source](https://developer.hashicorp.com/terraform/language/values/locals)). The syntax `local.<NAME>` evaluates to the expression assigned to that name ([source](https://developer.hashicorp.com/terraform/language/expressions/references)).

## Where can local values be used?

Local values can be used to set resource arguments such as `tags`, `subnet_id`, and `monitoring` inside a resource block ([source](https://developer.hashicorp.com/terraform/language/values/locals)). They can also be interpolated into strings, for example when naming a security group ([source](https://developer.hashicorp.com/terraform/language/values/locals)). Local values are scoped to the module where they are defined and cannot be accessed from other modules directly ([source](https://developer.hashicorp.com/terraform/language/values/locals)).

## When should you use a local value?

Use local values when a single value is reused in many places — so you can change it in one place — or when the value is the result of a complex expression that would be hard to read if repeated inline ([source](https://developer.hashicorp.com/terraform/language/values/locals)).

## Worked example

### Goal
Add a `locals` block that builds a `name_prefix` from two variables, then use it in the `tags` of both an S3 bucket and an EC2 instance.

---

**Step 1 — Identify the repeated expression.**

Both resources need a tag like `"myproject-prod"`. Without locals you would write `"${var.project}-${var.environment}"` in every `tags` block. That is exactly the kind of repeated expression a local value is designed to replace ([source](https://developer.hashicorp.com/terraform/language/values/locals)).

---

**Step 2 — Declare the `locals` block.**

```hcl
locals {
  name_prefix = "${var.project}-${var.environment}"
}
```

The block uses string interpolation of two input variables ([source](https://developer.hashicorp.com/terraform/language/values/locals)). Any valid expression is allowed here ([source](https://developer.hashicorp.com/terraform/language/values/locals)).

---

**Step 3 — Reference the local in each resource.**

Use `local.name_prefix` (singular `local`, not `locals`) wherever the prefix is needed ([source](https://developer.hashicorp.com/terraform/language/values/locals)):

```hcl
resource "aws_s3_bucket" "assets" {
  bucket = var.bucket_name

  tags = {
    Name = "${local.name_prefix}-assets"
  }
}

resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type

  tags = {
    Name = "${local.name_prefix}-app"
  }
}
```

Both resources draw from the same expression ([source](https://developer.hashicorp.com/terraform/language/values/locals)). If the project name ever changes, only the `locals` block needs updating.

---

**Step 4 — Run `terraform plan` and read the output.**

Terraform evaluates `local.name_prefix` during planning. In the plan output you will see something like:

```
+ tags = {
    + "Name" = "myproject-prod-assets"
  }
```

This confirms the local value resolved correctly before any infrastructure is created.

## Your turn

Add two new input variables — `project` (default `"myproject"`) and `environment` (default `"dev"`) — to `variables.tf`. Then create a `locals.tf` file that declares a single `locals` block containing one local value: `name_prefix`, built by joining `var.project` and `var.environment` with a hyphen using string interpolation. Finally, add a `tags` argument to both `aws_s3_bucket.assets` and `aws_instance.app` in `main.tf`. Each `tags` map must contain a `"Project"` key whose value is `local.name_prefix`. Run `terraform test` to confirm everything is wired up correctly.

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
