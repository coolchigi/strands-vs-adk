# Write the networking module

*Full VPC, Compute & Storage Stack*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the starter is not valid Terraform, so the learner would see a syntax error instead of a failing test: Error: Unsupported argument on main.tf line 4, in module "networking": 4: vpc_cidr = "10.0.0.0/16" An argument named "vpc_cidr" is not expected here. Error: Unsupported argument on main.tf line 5,...

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Write a networking module that creates a VPC, public subnets across AZs using cidrsubnet, an internet gateway, and route tables, with CIDR and AZ lists as input variables and vpc_id and subnet_ids as outputs

## Where we are

Earlier lessons introduced modules as a way to group related resources, established the flat module composition pattern where one module's outputs feed another module's inputs, and showed that provider blocks belong only in the root configuration — never inside a module.

## The idea

## Module file layout

The recommended filenames for a minimal module are `main.tf`, `variables.tf`, and `outputs.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). Input variable declarations belong in `variables.tf` and output value declarations belong in `outputs.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). Every variable and output should carry a one- or two-sentence description explaining its purpose ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

Variables declared without a default value are required — they must be supplied every time the module is called ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). Outputs are the only supported way for callers to get information about resources inside a module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

Because Terraform inherits the provider from the root configuration when it processes a module block, provider blocks must not appear inside modules ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

## Deriving subnet CIDRs with cidrsubnet

`cidrsubnet(prefix, newbits, netnum)` derives a subnet CIDR from a larger prefix ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)). The `newbits` argument adds that many bits to the prefix length — a `/16` with `newbits = 8` gives a `/24` ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)). The `netnum` argument picks which subnet to use within the extended space; it must fit in `newbits` binary digits ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)). Unlike `cidrsubnets`, `cidrsubnet` lets you specify the exact network number rather than always starting from zero ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)).

A practical pattern is `cidr_block = cidrsubnet(var.vpc_cidr, 8, count.index)` inside an `aws_subnet` resource that uses `count` — each subnet gets a unique `/24` derived from the VPC's `/16` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)).

## Internet gateway and route table

An internet gateway is attached to its VPC by setting `vpc_id` on `aws_internet_gateway` ([source](https://docs.aws.amazon.com/code-library/latest/ug/cli_2_ec2_code_examples.html)). Each public subnet needs a route table that sends `0.0.0.0/0` through the gateway, and an `aws_route_table_association` that links the route table to the subnet ([source](https://docs.aws.amazon.com/code-library/latest/ug/cli_2_ec2_code_examples.html)).

## Wiring it together with module composition

The networking module exposes `vpc_id` and `subnet_ids` as outputs so that sibling modules (compute, etc.) can consume them without reaching inside the module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). Passing those outputs as inputs to another module is the flat composition pattern ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)), and it means the compute module never needs to know how the network was built ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)).

## Worked example

## Goal

Build a networking module that creates a `/16` VPC, two public subnets in different AZs, an internet gateway, and a route table that routes `0.0.0.0/0` through the gateway.

---

### Step 1 — Declare the input variables (`variables.tf`)

```hcl
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
}

variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones in which to create public subnets."
}
```

No defaults: both are required, so a caller that omits either will get an error immediately ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

---

### Step 2 — Write the resources (`main.tf`)

```hcl
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
}

resource "aws_subnet" "public" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = var.availability_zones[count.index]
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
}

resource "aws_route_table_association" "public" {
  count          = length(var.availability_zones)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
```

**Why `cidrsubnet(var.vpc_cidr, 8, count.index)`?**
With a `/16` VPC and `newbits = 8`, the result is a `/24` ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)). `count.index` is `0`, `1`, `2` … giving `10.0.0.0/24`, `10.0.1.0/24`, `10.0.2.0/24` — each a unique, non-overlapping subnet ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)). The function works on the same addressing scheme as the input prefix ([source](https://developer.hashicorp.com/terraform/language/functions/cidrsubnet)).

The `aws_route_table_association` uses the same `count` as `aws_subnet.public`, so there is exactly one association per subnet ([source](https://docs.aws.amazon.com/code-library/latest/ug/cli_2_ec2_code_examples.html)).

---

### Step 3 — Expose outputs (`outputs.tf`)

```hcl
output "vpc_id" {
  description = "ID of the VPC created by this module."
  value       = aws_vpc.main.id
}

output "subnet_ids" {
  description = "List of public subnet IDs, one per availability zone."
  value       = aws_subnet.public[*].id
}

output "subnet_cidrs" {
  description = "List of public subnet CIDR blocks, one per availability zone."
  value       = aws_subnet.public[*].cidr_block
}
```

`subnet_ids` uses the splat expression `[*].id` to collect every subnet's ID into a list — the compute module can then pick from it or pass the whole list to an ALB ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

---

### Step 4 — Call the module from the root (`main.tf`)

```hcl
module "networking" {
  source             = "./modules/networking"
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
}
```

No provider block in the module — it inherits the root's AWS provider automatically ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

Running `terraform plan` from the root now shows `aws_vpc`, two `aws_subnet`, `aws_internet_gateway`, `aws_route_table`, and two `aws_route_table_association` resources planned — six resources total for two AZs.

## Your turn

Create a networking module at `modules/networking/` with three files.

**`modules/networking/variables.tf`** — declare three input variables:
- `vpc_cidr` (string) — the CIDR block for the VPC
- `availability_zones` (list of strings) — AZs in which to create subnets

**`modules/networking/main.tf`** — declare five resources (no provider block):
- `aws_vpc.main` using `var.vpc_cidr`
- `aws_subnet.public` with `count = length(var.availability_zones)`, deriving each CIDR with `cidrsubnet(var.vpc_cidr, 8, count.index)` and setting `availability_zone`
- `aws_internet_gateway.main` attached to the VPC
- `aws_route_table.public` with a `0.0.0.0/0` route through the gateway
- `aws_route_table_association.public` with `count` matching the subnets

**`modules/networking/outputs.tf`** — declare three outputs:
- `vpc_id` — the VPC's ID
- `subnet_ids` — list of subnet IDs (splat expression)
- `subnet_cidrs` — list of subnet CIDR blocks (splat expression)

Update the root `main.tf` to call `module "networking"` (source `./modules/networking`) instead of `module "network"`, passing `vpc_cidr = "10.0.0.0/16"` and `availability_zones = ["us-east-1a", "us-east-1b"]`. Update the root `outputs.tf` to reference `module.networking` outputs. Run `terraform test` from the root to verify.

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
