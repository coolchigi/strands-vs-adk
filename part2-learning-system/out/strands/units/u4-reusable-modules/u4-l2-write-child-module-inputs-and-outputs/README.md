# Write child module inputs and outputs

*Reusable Modules*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the checks don't test the gap at modules/compute/main.tf line 4: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Write a child module that accepts required input variables (no defaults) and exposes resource attributes as outputs, then consume those outputs in the root module
- Reference a child module's output in a root-level resource argument using the module.<NAME>.<OUTPUT> syntax

## Where we are

Earlier lessons showed how to call a child module from the root module using a `module` block with a `source` argument, and how the `modules/storage/` module exposes a `bucket_id` output that the root module reads. This lesson builds on that pattern by writing both the input variables and output values for new child modules from scratch.

## The idea

## Input variables in a child module

Modules use input variables to accept values from the calling module ([source](https://developer.hashicorp.com/terraform/language/modules/develop)). You declare them in the module's `variables.tf` using the same `variable` block syntax as the root module ([source](https://developer.hashicorp.com/terraform/language/modules/develop)). Any variable that has no `default` value is **required**: the caller must supply it every time the module is used, and Terraform will error if it is missing ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

```hcl
# modules/network/variables.tf
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  # no default → required
}
```

Module inputs are set by passing arguments inside the `module` block of the calling configuration — not through `-var` flags or `.tfvars` files ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

```hcl
# root main.tf
module "network" {
  source   = "./modules/network"
  vpc_cidr = "10.0.0.0/16"   # satisfies the required variable
}
```

## Output values in a child module

Modules use output values to return results to the calling module, which can then use them to populate arguments elsewhere ([source](https://developer.hashicorp.com/terraform/language/modules/develop)). You declare them in the module's `outputs.tf`. Outputs are the only supported way for callers to get information about resources configured inside a module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

```hcl
# modules/network/outputs.tf
output "subnet_id" {
  description = "ID of the created subnet."
  value       = aws_subnet.main.id
}
```

## Consuming a child module's output in the root module

Once a module declares an output, the root module references it with the expression `module.<MODULE-NAME>.<OUTPUT-NAME>` ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). That expression can appear anywhere a normal value is allowed — including as an argument to another module or resource ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)).

```hcl
# root main.tf — passing network output into compute module
module "compute" {
  source    = "./modules/compute"
  subnet_id = module.network.subnet_id
}
```

Terraform reads the dependency implied by that reference and automatically plans `module.network` before `module.compute` ([source](https://developer.hashicorp.com/terraform/language/modules/develop)). This is how you thread outputs from one module into inputs of another to express a cross-module dependency chain ([source](https://developer.hashicorp.com/terraform/tutorials/configuration-language/for-each)).

## Worked example

## Goal

Create a `modules/network/` module with a required `vpc_cidr` variable and a subnet output, then create a `modules/compute/` module with a required `subnet_id` variable, and wire them together in the root module.

---

### Step 1 — Write the network module's variable

`vpc_cidr` has no default, so it is required ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

```hcl
# modules/network/variables.tf
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
}
```

### Step 2 — Write the network module's resource

`cidrsubnet(var.vpc_cidr, 8, 0)` carves the first /24 out of whatever CIDR the caller passes in.

```hcl
# modules/network/main.tf
resource "aws_subnet" "main" {
  vpc_id     = aws_vpc.main.id
  cidr_block = cidrsubnet(var.vpc_cidr, 8, 0)
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr
}
```

### Step 3 — Expose the subnet id as an output

Outputs are the only way for callers to read attributes of resources inside the module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

```hcl
# modules/network/outputs.tf
output "subnet_id" {
  description = "ID of the subnet created by this module."
  value       = aws_subnet.main.id
}
```

### Step 4 — Write the compute module's variable and resource

`subnet_id` has no default, so it too is required ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

```hcl
# modules/compute/variables.tf
variable "subnet_id" {
  type        = string
  description = "ID of the subnet to place the instance in."
}
```

```hcl
# modules/compute/main.tf
resource "aws_instance" "app" {
  ami           = "ami-0deadbeef00000000"
  instance_type = "t3.micro"
  subnet_id     = var.subnet_id
}
```

### Step 5 — Call both modules in the root, threading the output through

`module.network.subnet_id` uses the `module.<NAME>.<OUTPUT>` syntax ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)) to pass the network module's subnet id directly into the compute module's required variable.

```hcl
# root main.tf (additions)
module "network" {
  source   = "./modules/network"
  vpc_cidr = "10.0.0.0/16"
}

module "compute" {
  source    = "./modules/compute"
  subnet_id = module.network.subnet_id   # cross-module reference
}
```

### Step 6 — Verify the plan

```
$ terraform init   # picks up the two new module directories
$ terraform plan
```

Terraform plans `aws_vpc.main` and `aws_subnet.main` (inside `module.network`) first, then `aws_instance.app` (inside `module.compute`), because the `module.network.subnet_id` reference creates an implicit dependency. No extra `depends_on` is needed.

## Your turn

Create two new child modules and wire them together.

1. **`modules/network/`** — declare a required string variable `vpc_cidr` (no default). Create an `aws_vpc` resource using `var.vpc_cidr` and an `aws_subnet` resource whose `cidr_block` is `cidrsubnet(var.vpc_cidr, 8, 0)`. Output the subnet's id as `subnet_id` and the subnet's cidr_block as `subnet_cidr`.

2. **`modules/compute/`** — declare a required string variable `subnet_id` (no default). Create an `aws_instance` resource with `ami = "ami-0deadbeef00000000"`, `instance_type = "t3.micro"`, and `subnet_id = var.subnet_id`. Output the instance id as `instance_id`.

3. **Root `main.tf`** — add a `module "network"` block that passes `vpc_cidr = "10.0.0.0/16"`, and a `module "compute"` block that passes `subnet_id = module.network.subnet_id`.

4. **Root `outputs.tf`** — add outputs `network_subnet_id` (value: `module.network.subnet_id`) and `compute_instance_id` (value: `module.compute.instance_id`).

Run `terraform init` then `terraform apply` (or run the test suite with `terraform test`).

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
