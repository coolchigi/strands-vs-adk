# Inter-Module Data Flow and Multi-Instance Scaling

*Modular Infrastructure Architecture*

## By the end of this lesson you can

- Pass input values into child modules and consume child module outputs in parent and sibling modules
- Scale child module deployments using count and for_each meta-arguments

## Where we are

Earlier lessons established how to encapsulate AWS resources into child modules such as VPCs and define clear inputs and outputs. You also learned how to define root configuration files and reference attributes across resource blocks.

## The idea

Module authors expose inputs that you can configure as arguments within a module block to customize its behavior without modifying source code ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). Variable declarations should be kept in `variables.tf`, and output declarations should be kept in `outputs.tf` ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

Values from child module outputs can be accessed in the parent module using the expression syntax `module.<MODULE-NAME>.<OUTPUT-NAME>` ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). A parent module can configure a module by providing arguments within its module block using these child module output expressions ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)) ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)).

Any input variable referenced inside a module block's `source` or `version` arguments must declare `const = true` ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)).

The `count` meta-argument can be added to a module block to state how many instances of a module to provision, with all instances having the same configuration ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). The `for_each` meta-argument allows looping through a set of keys so that Terraform provisions similar module instances ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). To change a resource address and move a resource into a child module without destroying and recreating it, you can use the `moved` block ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)).

## Worked example

Consider an architecture where a networking module defines a VPC and subnets, and a database module must deploy into those subnets across different environments.

First, inside the networking module (`modules/networking/outputs.tf`), you export the subnet identifier:
```hcl
output "subnet_id" {
  description = "The ID of the database subnet"
  value       = aws_subnet.database.id
}
```

Next, in the database module (`modules/database/variables.tf`), you declare the required input:
```hcl
variable "subnet_id" {
  type        = string
  description = "Target subnet for database instances"
}

variable "tier" {
  type        = string
  description = "Environment tier name"
}
```

In the root `main.tf`, you instantiate the networking module first, then wire its output into the database module while scaling across tiers using `for_each`:
```hcl
module "networking" {
  source = "./modules/networking"
}

module "database" {
  source   = "./modules/database"
  for_each = toset(["primary", "replica"])

  subnet_id = module.networking.subnet_id
  tier      = each.key
}
```

Because `module.database` uses `for_each`, Terraform creates individual instances addressable as `module.database["primary"]` and `module.database["replica"]`. To collect an output across all instances in the root `outputs.tf`, use a `for` expression:
```hcl
output "database_endpoint_map" {
  value = { for tier, db in module.database : tier => db.endpoint }
}
```
This enables clean data flow from the networking module into the database module and exposes the aggregated results back to the root module.

## Your turn

Extract the compute configuration into a reusable `modules/compute` child module and scale it using `for_each`.

1. In `modules/compute/outputs.tf`, export `instance_id` with the value of `aws_instance.web.id`.
2. In the root `main.tf`, configure the `module "compute"` block:
   - Set `for_each` to `var.instance_types`.
   - Wire `subnet_id` using the `public_subnet_id` output from `module.vpc`.
   - Set `instance_type` to `each.value`.
   - Set `environment` to `each.key`.
3. In the root `outputs.tf`, complete `compute_instance_ids` by returning a map where each environment key points to its compute module `instance_id` output using a `for` expression.

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
