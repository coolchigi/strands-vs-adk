# Reference attributes across blocks and use built-in functions

*HashiCorp Configuration Language (HCL)*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - u2-l5: 'Predict the CIDR output of a cidrsubnet call given a parent prefix, newbits, and netnum' asks the learner to analyze, and a quiz can't show that. It needs an exercise.
> - The worked example's Step 3 locals block uses `var.project` and `var.environment` (in `name_prefix`) but Step 1 only declares `vpc_cidr` and `availability_zones`. A learner following the worked example in isolation has a broken configuration — those two variables are never declared in the example....
> - The `subnet_count_local_uses_length` check is a tautology: it asserts `local.subnet_count == length(var.availability_zones)`. Because `var.availability_zones` defaults to a three-element list, a learner who hardcodes `subnet_count = 3` passes this check just as easily as one who writes...
> - question 1's explanation names an option by its position ("Option A"), and learn.py numbers options from 1. Name it by what it says.
> - question 3's explanation names an option by its position ("Option A"), and learn.py numbers options from 1. Name it by what it says.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Reference resource attributes across blocks using dot-notation expressions and implicit dependency, and compute subnet CIDRs using cidrsubnet and length
- Predict the CIDR output of a cidrsubnet call given a parent prefix, newbits, and netnum

## Where we are

Earlier lessons established that Terraform resources are declared with `resource` blocks, that `locals` hold computed values, and that `output` blocks expose values from the configuration. You also learned that `variable` blocks declare inputs and that `terraform.tfvars` supplies their values.

## The idea

## Referencing resource attributes across blocks

Every managed resource is identified by its type and name label. To read one of its attributes inside another block, write `<TYPE>.<NAME>.<ATTRIBUTE>` ([source](https://developer.hashicorp.com/terraform/language/expressions/references))([source](https://developer.hashicorp.com/terraform/language/block/resource)). For example, `aws_subnet.public.id` reads the `id` attribute that the subnet resource exports after it is created ([source](https://developer.hashicorp.com/terraform/language/expressions/references)).

When an expression in one resource block refers to another resource this way, Terraform records an **implicit dependency** between them and uses it to infer the correct order of operations — no `depends_on` is needed ([source](https://developer.hashicorp.com/terraform/language/expressions/references)).

## The cidrsubnet function

`cidrsubnet(prefix, newbits, netnum)` carves a single subnet out of a parent CIDR block ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)). The `prefix` must be supplied in CIDR notation ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)).

`newbits` says how many extra bits to add to the prefix length. A `/16` parent with `newbits = 8` produces a `/24` child ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)). `netnum` picks which of the possible subnets you want; it is encoded into those extra bits ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)). The function works with both IPv4 and IPv6, and the result always matches the addressing scheme of the input ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)).

## The length function

`length()` returns the number of elements in a list, map, or string. Inside a `locals` block you can write `subnet_count = length(var.availability_zones)` to derive a count from any collection ([source](https://developer.hashicorp.com/terraform/tutorials/configuration-language/for-each)).

## Worked example

### Goal
Given a VPC with CIDR `10.0.0.0/16`, create a subnet whose CIDR is computed with `cidrsubnet`, and expose its id in an output. Also compute `subnet_count` from a list of AZs.

### Step 1 — declare the variables

```hcl
# variables.tf
variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b", "us-east-1c"]
}
```

### Step 2 — create the VPC and subnet

```hcl
# main.tf
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
}

resource "aws_subnet" "public" {
  vpc_id     = aws_vpc.main.id                       # dot-notation reference
  cidr_block = cidrsubnet(var.vpc_cidr, 8, 1)        # 10.0.1.0/24
}
```

`aws_vpc.main.id` creates an implicit dependency: Terraform will create the VPC before the subnet ([source](https://developer.hashicorp.com/terraform/language/expressions/references)). `cidrsubnet("10.0.0.0/16", 8, 1)` adds 8 bits to the /16 prefix (giving /24) and picks netnum 1, so the result is `10.0.1.0/24` ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet))([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)).

### Step 3 — compute subnet_count in locals

```hcl
# locals.tf
locals {
  name_prefix  = "${var.project}-${var.environment}"
  subnet_count = length(var.availability_zones)      # evaluates to 3
}
```

### Step 4 — output the subnet id

```hcl
# outputs.tf
output "subnet_id" {
  description = "ID of the public subnet"
  value       = aws_subnet.public.id
}
```

`aws_subnet.public.id` uses the same dot-notation to read an exported attribute ([source](https://developer.hashicorp.com/terraform/language/expressions/references)).

### Verify mentally

`cidrsubnet("10.0.0.0/16", 8, 1)`:
- parent prefix length = 16, newbits = 8 → result prefix = /24 ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet))
- netnum = 1, encoded into the 8 new bits → third octet = 1
- result: `10.0.1.0/24` ✓

## Your turn

Starting from the files below, do three things:
1. In `main.tf`, add an `aws_subnet` resource named `public` whose `vpc_id` is taken from `aws_vpc.main.id` (dot-notation) and whose `cidr_block` is computed with `cidrsubnet(var.vpc_cidr, 8, 1)`.
2. In `locals.tf`, add a local value `subnet_count` equal to `length(var.availability_zones)`.
3. In `outputs.tf`, add an output named `subnet_id` whose value is `aws_subnet.public.id`.

Run `terraform init` then `terraform apply` (or run the tests with `terraform test`) to verify.

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
