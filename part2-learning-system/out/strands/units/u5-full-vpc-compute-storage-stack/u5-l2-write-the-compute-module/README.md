# Write the compute module

*Full VPC, Compute & Storage Stack*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the exercise has no .tftest.hcl checks

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Write a compute module that creates EC2 instances using subnet IDs and instance type received from the networking module's outputs, with count to create multiple instances

## Where we are

The networking module outputs `subnet_ids` as a list, one per availability zone. Modules receive their dependencies from the root module rather than creating them — the root wires outputs from one module into inputs of another. Earlier lessons established that modules have `variables.tf`, `main.tf`, and `outputs.tf`.

## The idea

## Module file layout

The recommended filenames for a minimal module are `main.tf`, `variables.tf`, and `outputs.tf`, even if they are empty ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). Input variable declarations belong in `variables.tf` and output value declarations belong in `outputs.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). All variables and outputs should have one or two sentence descriptions explaining their purpose ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

## Declaring variables

Variables declared in a module without a default value are required and must be set every time the module is used ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). A variable *with* a default is optional — the caller may omit it and the default applies ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). For the compute module we need three variables: `ami_id` (required, no default), `subnet_ids` (required, typed `list(string)`), and `instance_type` (optional, defaulting to `"t3.micro"`).

## Using `count` to create multiple instances

Two or more EC2 instances can be created by setting the `count` meta-argument on an `aws_instance` resource ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)). Setting `count = length(var.subnet_ids)` produces exactly one instance per subnet. Inside the resource block, `count.index` is the zero-based position of the current instance, so `subnet_id = var.subnet_ids[count.index]` places each instance in a different subnet ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)). A resource block for an EC2 instance requires at minimum the `ami` and `instance_type` arguments ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

## Wiring outputs to the root module

Outputs are the only supported way for users to get information about resources configured inside a module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). Because `aws_instance.app` is now a list (due to `count`), the splat expression `aws_instance.app[*].id` collects all instance IDs into a list ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)). The root module passes networking outputs into the compute module: `subnet_ids = module.networking.subnet_ids` expresses the cross-module dependency ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)).

## Provider blocks do not belong in modules

When Terraform processes a module block it inherits the provider from the enclosing configuration, so provider blocks should not be included inside modules ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

## Worked example

### Goal

Create a compute module that launches one EC2 instance per subnet, then wire it into the root module.

---

**Step 1 — declare variables (`modules/compute/variables.tf`)**

We need three inputs. `subnet_ids` is a required list; `instance_type` has a safe default; `ami_id` is required because AMI IDs are region-specific and the module shouldn't hard-code one.

```hcl
variable "ami_id" {
  type        = string
  description = "AMI ID to use for each EC2 instance."
}

variable "subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs; one instance is created in each subnet."
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for every instance in the module."
  default     = "t3.micro"
}
```

`ami_id` and `subnet_ids` have no default, so they are required every time this module is used ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)).

---

**Step 2 — create instances with `count` (`modules/compute/main.tf`)**

```hcl
resource "aws_instance" "app" {
  count         = length(var.subnet_ids)   # one instance per subnet
  ami           = var.ami_id
  instance_type = var.instance_type
  subnet_id     = var.subnet_ids[count.index]  # distributes across subnets
}
```

`count = length(var.subnet_ids)` means: if the networking module produced two subnets, Terraform plans two instances ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)). `count.index` is 0 for the first instance and 1 for the second, so each lands in a different subnet.

---

**Step 3 — expose outputs (`modules/compute/outputs.tf`)**

```hcl
output "instance_ids" {
  description = "List of IDs of the EC2 instances created by this module."
  value       = aws_instance.app[*].id
}

output "public_ips" {
  description = "List of public IP addresses of the EC2 instances."
  value       = aws_instance.app[*].public_ip
}
```

The splat `[*].id` collects every instance's ID into a list, matching the shape callers expect ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)).

---

**Step 4 — wire into the root module (`main.tf`)**

```hcl
module "compute" {
  source    = "./modules/compute"

  ami_id     = "ami-0c55b159cbfafe1f0"
  subnet_ids = module.networking.subnet_ids   # all subnets from networking
}
```

`module.networking.subnet_ids` is the output from the networking module; passing it here creates the cross-module dependency Terraform uses to sequence the apply ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)).

---

**Verification reasoning**

After `terraform apply`, `module.compute.instance_ids` is a list with one entry per subnet. The networking module was configured with `availability_zones = ["us-east-1a", "us-east-1b"]`, so two subnets exist → two instances are created, one in each AZ.

## Your turn

Upgrade the compute module so it creates one EC2 instance per subnet using `count`, then update the root module to pass all subnet IDs.

1. **`modules/compute/variables.tf`** — replace the single `subnet_id` variable with three variables: `ami_id` (string, required), `subnet_ids` (list(string), required), and `instance_type` (string, default `"t3.micro"`).
2. **`modules/compute/main.tf`** — set `count = length(var.subnet_ids)` on `aws_instance.app`, use `var.ami_id`, `var.instance_type`, and `var.subnet_ids[count.index]`.
3. **`modules/compute/outputs.tf`** — replace the single `instance_id` output with `instance_ids` (list from splat `[*].id`) and add `public_ips` (list from splat `[*].public_ip`).
4. **`main.tf`** (root) — update the `compute` module block to pass `ami_id`, `subnet_ids = module.networking.subnet_ids`, and remove the old `subnet_id` argument.
5. **`outputs.tf`** (root) — replace `compute_instance_id` with `compute_instance_ids` that references `module.compute.instance_ids`.

Run `terraform init && terraform test` to verify.

Nothing can check this exercise automatically, so you're the judge. When you're happy with it, `learn check` marks it done and `learn solution` shows the answer.

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
