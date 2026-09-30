# Declare required_providers and pin the AWS provider version

*Install, Configure & Initialise*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the untouched starter already passes the checks, so there is nothing to do
> - question 1's explanation names an option by its position ("option 3"), and learn.py numbers options from 1. Name it by what it says.
> - question 2's explanation names an option by its position ("Option 1"), and learn.py numbers options from 1. Name it by what it says.
> - question 3's explanation names an option by its position ("option 1)"), and learn.py numbers options from 1. Name it by what it says.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Write a terraform block containing a required_providers entry that pins the hashicorp/aws provider to a specific version constraint
- Explain what the ~> version constraint operator means and why pinning provider versions matters

## Where we are

The previous lesson confirmed that Terraform is installed and working by writing a `locals` block and an `output` block in `main.tf`. Those two block types are always available with no provider needed. This lesson adds the `terraform {}` configuration block, which lives alongside them but controls Terraform itself.

## The idea

## The `terraform` block

The top-level `terraform {}` block is where you configure Terraform's own behaviour for a project. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)) One of its most important settings is `required_version`, which constrains which versions of Terraform itself are acceptable; the string `>= 1.2` means any Terraform version 1.2 or higher is allowed. ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create))

The convention is to keep this block in a dedicated `terraform.tf` file rather than mixing it into `main.tf`. ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create))

## Declaring a provider with `required_providers`

Providers are plugins that let Terraform talk to APIs such as AWS. You declare them inside a `required_providers` block nested inside the `terraform {}` block. ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create)) Each entry uses a local name as the key (e.g. `aws`) and an object with `source` and `version` as the value. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements))

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

The `source` argument is the provider's global address: an optional hostname, a namespace, and a type. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)) Writing `hashicorp/aws` is shorthand for `registry.terraform.io/hashicorp/aws`; the hostname defaults to the public Terraform Registry when omitted. ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create)) ([source](https://developer.hashicorp.com/terraform/language/providers/requirements))

The `version` argument constrains which versions Terraform may install. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)) It is technically optional, but strongly recommended for every provider. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)) Without it, Terraform installs the most recent version available. ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create))

## The `~>` pessimistic constraint operator

The `~>` operator pins the rightmost version component you specify and allows only the components to its right to increment. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements))

- `~> 6.0` — pins the major version to 6; minor and patch are free to grow, so `6.1.3`, `6.99.0` etc. are all allowed, but `7.0.0` is not. ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create))
- `~> 1.0.4` — pins major and minor; only the patch component can increment, so `1.0.5` is allowed but `1.1.0` is not. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements))

For a root module (where you run `terraform apply`) it is recommended to specify both a minimum and a maximum, which the `~>` operator achieves in one expression. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements))

## Worked example

**Goal:** add a `terraform.tf` file that pins Terraform itself to `>= 1.1.0` and pins the AWS provider to `~> 6.0`.

**Step 1 — create the file and open the `terraform` block.**

The block is always named `terraform`; there are no labels.

```hcl
terraform {

}
```

**Step 2 — add `required_version`.**

We want any Terraform 1.1.0 or later, so the `>=` operator is correct here. ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create))

```hcl
terraform {
  required_version = ">= 1.1.0"
}
```

**Step 3 — add the `required_providers` block.**

It must be nested inside the `terraform {}` block. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)) The local name `aws` is the key; `source` and `version` go inside the object. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements))

```hcl
terraform {
  required_version = ">= 1.1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
```

**Step 4 — verify the HCL is well-formed.**

Run `terraform fmt` in the project directory. If the file has syntax errors, `fmt` will report them. If it succeeds (exit 0), the HCL is valid. The command also rewrites the file with canonical indentation, so running it is always safe.

**Why `~> 6.0` and not `= 6.0`?**

Using `= 6.0` would freeze us on exactly one version forever. ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)) `~> 6.0` allows any `6.x.y` release, so we get bug-fix and feature updates within the major version automatically, but we are protected from a future `7.0` release that might have breaking changes. ([source](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-create))

## Your turn

In the project directory from lesson 1, create a file called `terraform.tf` that contains a single `terraform {}` block. Inside it, set `required_version = ">= 1.1.0"` and add a `required_providers` block that declares the `aws` provider with `source = "hashicorp/aws"` and `version = "~> 6.0"`. Keep `main.tf` exactly as it is. Run `terraform fmt` to confirm the file is valid HCL.

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
