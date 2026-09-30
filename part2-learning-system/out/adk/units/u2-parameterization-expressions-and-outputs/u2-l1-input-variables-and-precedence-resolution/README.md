# Input Variables and Precedence Resolution

*Parameterization, Expressions, and Outputs*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - u2-l1: 'Predict variable value assignment according to Terraform precedence rules across CLI flags, tfvars, and environment variables' asks the learner to analyze, and a quiz can't show that. It needs an exercise.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Define input variables with type constraints, default values, descriptions, and custom validation blocks
- Predict variable value assignment according to Terraform precedence rules across CLI flags, tfvars, and environment variables

## Where we are

In earlier lessons, we defined AWS resources—including a VPC, subnets, route tables, and an S3 bucket—using hardcoded configuration values. We also configured provider settings with local endpoint overrides to mock and validate infrastructure without incurring cloud costs.

## The idea

Input variables parameterize Terraform configurations and can include type constraints, human-readable descriptions, and default values ([source](https://developer.hashicorp.com/terraform/language/values/variables)). When an input variable does not specify a default value, Terraform prompts the user to enter one before generating a plan ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Within configurations, variable values are accessed using the `var.<NAME>` syntax ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

Variables also support access controls and custom constraints. Custom validation rules can be added to variable definitions using a `validation` block that specifies a `condition` and an `error_message` ([source](https://developer.hashicorp.com/terraform/language/values/variables)). To prevent sensitive values from appearing in CLI output, set `sensitive = true` on the variable definition ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Furthermore, adding the `ephemeral` argument excludes the variable from state and plan files ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

Terraform provides several mechanisms to populate root module variables. Values can be assigned using environment variables prefixed with `TF_VAR_` ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Terraform automatically loads variable definitions from files named `terraform.tfvars`, `terraform.tfvars.json`, or files ending in `.auto.tfvars` or `.auto.tfvars.json` ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Additionally, values can be supplied directly on the command line using the `-var=<VAR_NAME>=<VALUE>` flag ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

When multiple sources assign a value to the same variable, Terraform resolves the conflict using a strict order of precedence from highest to lowest ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Command-line `-var` and `-var-file` options (along with HCP Terraform) hold the highest priority, followed by `*.auto.tfvars` files in lexical order, `terraform.tfvars.json`, `terraform.tfvars`, `TF_VAR_` environment variables, and finally the `default` argument in the variable block ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

## Worked example

### Declaring and Validating Variables

Suppose you want to parameterize the deployment environment for your infrastructure. In `variables.tf`, declare the variable with a type constraint, a description, a default value, and a custom validation block:

```hcl
variable "environment" {
  type        = string
  description = "Deployment environment name"
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}
```

In `main.tf`, reference this variable when naming resources:

```hcl
resource "aws_s3_bucket" "app_storage" {
  bucket = "my-app-${var.environment}-data"
}
```

### Resolving Value Precedence

Consider what happens when multiple configuration sources provide values for `var.environment` simultaneously:

1. In `variables.tf`: `default = "dev"`
2. In shell session: `export TF_VAR_environment="staging"`
3. In `terraform.tfvars`: `environment = "prod"`
4. At execution: `terraform apply -var="environment=dev"`

Terraform determines the final value by evaluating sources in precedence order:
- `default = "dev"` is lowest precedence (level 6).
- `TF_VAR_environment="staging"` overrides the default (level 5).
- `terraform.tfvars` (`prod`) overrides the environment variable (level 4).
- The CLI flag `-var="environment=dev"` has highest precedence (level 1).

Terraform assigns `"dev"` to `var.environment`. Next, the `validation` block checks whether `"dev"` is in `["dev", "staging", "prod"]`. The condition evaluates to `true`, validation succeeds, and the plan proceeds.

## Your turn

Extract the hardcoded CIDR blocks in `main.tf` into `variables.tf` and add custom validation.

1. In `variables.tf`, add a `validation` block to both `var.vpc_cidr` and `var.public_subnet_cidr`. Use the condition `can(cidrnetmask(var.<NAME>))` to ensure the value is a valid IPv4 CIDR string, with an appropriate `error_message`.
2. In `main.tf`, replace the hardcoded CIDR string on `aws_vpc.main.cidr_block` with `var.vpc_cidr`.
3. In `main.tf`, replace the hardcoded CIDR string on `aws_subnet.public.cidr_block` with `var.public_subnet_cidr`.

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
