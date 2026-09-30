# Parameterise with input variables

*HashiCorp Configuration Language (HCL)*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - u2-l2: 'Choose between -var flag, .tfvars file, and TF_VAR_ environment variable to supply a value, explaining the precedence order' asks the learner to analyze, and a quiz can't show that. It needs an exercise.
> - The Precedence section ranks -var > .tfvars > default but never states where TF_VAR_ sits in that order. The stated objective is to explain the full precedence order, and environment variables are listed as one of the three supply methods, so the omission leaves the explanation short of what the...
> - No quiz question tests where TF_VAR_ falls in the precedence order. Q2 tests undeclared-variable behaviour (silent ignore), which is a different property. The objective explicitly includes 'explaining the precedence order' for all three supply methods, so a question distinguishing TF_VAR_ from -var...

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Declare input variables with type, description, default, and validation, then reference them inside resource arguments using var.<NAME>
- Choose between -var flag, .tfvars file, and TF_VAR_ environment variable to supply a value, explaining the precedence order

## Where we are

The previous lesson established that a Terraform configuration is made up of resource blocks, and that `terraform plan` shows what changes Terraform will make before you apply them. We also set up a local AWS provider pointing at LocalStack so no real cloud account is needed.

## The idea

## Declaring input variables

A `variable` block is how you introduce a named input into your configuration. Each block can declare `type`, `description`, and `default` arguments ([source](https://developer.hashicorp.com/terraform/language/values/variables)). If you omit `default`, Terraform will stop and prompt you for a value before it generates a plan ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

```hcl
variable "instance_type" {
  type        = string
  description = "EC2 instance type for the web server"
  default     = "t3.micro"
}
```

When you declare a `type` constraint, Terraform automatically converts a caller-supplied value to match it, so the value you get from `var.<NAME>` always conforms to the declared type ([source](https://developer.hashicorp.com/terraform/language/expressions/references)).

## Adding validation

A `variable` block can include an optional `validation` block containing a `condition` expression and an `error_message` ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Terraform evaluates the condition when a value is provided; if it is `false`, the error message is displayed and the operation stops.

```hcl
variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket"

  validation {
    condition     = length(var.bucket_name) > 0
    error_message = "bucket_name must not be empty."
  }
}
```

## Referencing variables

Inside resource arguments you reference an input variable with `var.<NAME>` ([source](https://developer.hashicorp.com/terraform/language/values/variables)). The same syntax works as a direct argument value or embedded in a string template ([source](https://developer.hashicorp.com/terraform/language/values/variables)):

```hcl
resource "aws_instance" "app" {
  instance_type = var.instance_type          # direct value
  tags = {
    Name = "${var.instance_type}-server"     # inside a string template
  }
}
```

## Supplying values

There are three common ways to supply a value at runtime:

| Method | Example |
|---|---|
| `-var` flag | `terraform apply -var="instance_type=t3.small"` |
| `.tfvars` file | `terraform.tfvars` (auto-loaded) or `-var-file="prod.tfvars"` |
| Environment variable | `export TF_VAR_instance_type=t3.small` |

The `-var` flag sets a variable directly on the command line ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Variable definition files use a `.tfvars` or `.auto.tfvars` extension and let you assign many variables in one place ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Terraform automatically loads `terraform.tfvars`, `terraform.tfvars.json`, and any file ending in `.auto.tfvars` ([source](https://developer.hashicorp.com/terraform/language/values/variables)); you can also pass a specific file with `-var-file` ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Environment variables prefixed with `TF_VAR_` followed by the variable name are a third option ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

## Precedence

The three methods above are not equal. The command-line `-var` flag takes the highest precedence; `.tfvars` file values sit in the middle; and the `default` argument of the variable block is the lowest precedence ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

One behavioural difference to remember: Terraform raises an **error** if you use `-var` for an undeclared variable, prints a **warning** for an undeclared variable in a `.tfvars` file, and **silently ignores** an undeclared `TF_VAR_` environment variable ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

## Worked example

## Worked example: parameterising a bucket name

**Goal:** move a hard-coded bucket name into an input variable with a validation rule, then override it via `terraform.tfvars`.

---

### Step 1 — Declare the variable in `variables.tf`

```hcl
variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket to create"
  default     = "tf-learn-assets-bucket"

  validation {
    condition     = length(var.bucket_name) > 0
    error_message = "bucket_name must not be empty."
  }
}
```

`type = string` tells Terraform what kind of value to expect. The `default` means the variable is optional — Terraform uses `"tf-learn-assets-bucket"` if nothing else is provided. The `validation` block rejects the empty-string case before any API call is made.

---

### Step 2 — Reference the variable in `main.tf`

```hcl
resource "aws_s3_bucket" "assets" {
  bucket = var.bucket_name   # reads the input variable
}
```

`var.bucket_name` is the standard way to read an input variable inside a resource argument ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Because the declared type is `string`, Terraform guarantees the value conforms to that type even if the caller passed something that needed conversion ([source](https://developer.hashicorp.com/terraform/language/expressions/references)). You could equally write `"${var.bucket_name}"` inside a string template — same variable, different context ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

---

### Step 3 — Supply an override in `terraform.tfvars`

```hcl
bucket_name = "my-project-assets-2024"
```

Terraform auto-loads this file ([source](https://developer.hashicorp.com/terraform/language/values/variables)). Because a `.tfvars` value overrides the `default`, the bucket will be named `"my-project-assets-2024"` ([source](https://developer.hashicorp.com/terraform/language/values/variables)).

---

### Step 4 — Verify with `terraform plan`

Running `terraform plan` shows:

```
  + resource "aws_s3_bucket" "assets" {
      + bucket = "my-project-assets-2024"
      ...
    }
```

The plan confirms the overridden value is in use. If you removed the value from `terraform.tfvars` and ran `terraform plan -var="bucket_name="` (empty string), the validation block would fire:

```
│ Error: Invalid value for variable
│   on variables.tf line 1:
│   1: variable "bucket_name" {
│ bucket_name must not be empty.
```

## Your turn

Create `variables.tf` with two input variables — `bucket_name` (string, with a description, a default of `"tf-learn-assets-bucket"`, and a validation block that rejects an empty string) and `instance_type` (string, with a description and a default of `"t3.micro"`). Update `main.tf` to replace the hard-coded bucket name and instance type with `var.bucket_name` and `var.instance_type`. Create `terraform.tfvars` and set `bucket_name` to `"my-learn-assets-2024"`. Run `terraform init` then the tests.

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
