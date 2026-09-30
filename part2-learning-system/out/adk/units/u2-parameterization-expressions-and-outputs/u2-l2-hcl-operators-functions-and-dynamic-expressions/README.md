# HCL Operators, Functions, and Dynamic Expressions

*Parameterization, Expressions, and Outputs*

## By the end of this lesson you can

- Evaluate expressions and built-in functions interactively using the terraform console command
- Construct dynamic resource arguments combining conditional logic, collection transformations, and template functions

## Where we are

In earlier lessons, we defined AWS provider blocks, declared network infrastructure using resources like VPCs and subnets, and added input variables with validation rules using the can function. We also linked resource attributes together through expression references.

## The idea

You can test and evaluate Terraform built-in functions interactively using the terraform console command ([source](https://developer.hashicorp.com/terraform/language/functions)). The general syntax for calling a function in Terraform is the function name followed by comma-separated arguments enclosed in parentheses ([source](https://developer.hashicorp.com/terraform/language/functions)). The Terraform configuration language does not allow user-defined functions directly in the configuration, but custom providers can be developed to expose functions ([source](https://developer.hashicorp.com/terraform/language/functions)). When calling a provider-specific function, the call must be prefixed with provider::<local-name>:: where local-name matches an entry in the required_providers block ([source](https://developer.hashicorp.com/terraform/language/functions)).

Arithmetic operators (+, -, *, /, %, and unary -) expect number values and produce number values ([source](https://developer.hashicorp.com/terraform/language/expressions/operators)). The % operator returns the remainder of dividing a by b ([source](https://developer.hashicorp.com/terraform/language/expressions/operators)). Comparison operators (<, <=, >, >=) expect number values and produce boolean values ([source](https://developer.hashicorp.com/terraform/language/expressions/operators)). Equality operators (== and !=) take values of any type and produce boolean results, returning true for == only if both values have the exact same type and value ([source](https://developer.hashicorp.com/terraform/language/expressions/operators)). Logical operators (||, &&, !) expect bool values and return bool results ([source](https://developer.hashicorp.com/terraform/language/expressions/operators)). Terraform does not include an exclusive OR operator, but for boolean values, exclusive OR is equivalent to using the != operator ([source](https://developer.hashicorp.com/terraform/language/expressions/operators)). When multiple operators are used together, Terraform evaluates them in order: unary !, -; then *, /, %; then +, -; then >, >=, <, <=; then ==, !=; then &&; then || ([source](https://developer.hashicorp.com/terraform/language/expressions/operators)). Parentheses can be used to override the default operator order of operations in Terraform ([source](https://developer.hashicorp.com/terraform/language/expressions/operators)). The ? and : characters form conditional expressions in Terraform and are not considered operators ([source](https://developer.hashicorp.com/terraform/language/expressions/operators)).

The lookup function retrieves the value of a single element from a map based on a given key ([source](https://developer.hashicorp.com/terraform/language/functions)). The merge function accepts an arbitrary number of maps or objects and returns a single merged map or object ([source](https://developer.hashicorp.com/terraform/language/functions)). The flatten function takes a list and eliminates nested lists by replacing them with a flattened sequence of their contents ([source](https://developer.hashicorp.com/terraform/language/functions)). The coalesce function takes multiple arguments and returns the first argument that is neither null nor an empty string ([source](https://developer.hashicorp.com/terraform/language/functions)). The file function reads the contents of a file located at a given path and returns them as a string ([source](https://developer.hashicorp.com/terraform/language/functions)). The templatefile function reads a file at a specified path and renders its contents as a template with a provided set of template variables ([source](https://developer.hashicorp.com/terraform/language/functions)). The try function evaluates expressions in sequence and returns the result of the first expression that does not raise an error ([source](https://developer.hashicorp.com/terraform/language/functions)). The can function evaluates an expression and returns a boolean indicating whether it evaluated without errors ([source](https://developer.hashicorp.com/terraform/language/functions)).

## Worked example

### Step 1: Experimenting interactively in the console

Launch `terraform console` to test expressions and built-in functions interactively:

```text
$ terraform console
> lookup({ dev = "t3.micro", prod = "m5.large" }, "dev", "t3.nano")
"t3.micro"

> merge({ Project = "Apollo", Env = "dev" }, { Env = "staging", Tier = "api" })
{
  "Env" = "staging"
  "Project" = "Apollo"
  "Tier" = "api"
}
```

Notice how `merge` takes multiple maps and merges them left-to-right, overwriting identical keys (`Env` becomes `"staging"`).

### Step 2: Creating a reusable template

Next, create a template file `bootstrap.sh.tftpl` on disk:

```bash
#!/bin/bash
echo "Bootstrapping node for ${cluster_name}"
```

In `terraform console`, verify how `templatefile` renders it:

```text
> templatefile("${path.module}/bootstrap.sh.tftpl", { cluster_name = "prod-cluster" })
<<EOT
#!/bin/bash
echo "Bootstrapping node for prod-cluster"

EOT
```

### Step 3: Assembling dynamic resource arguments

In your `.tf` files, wire these functions directly into the resource declaration:

```hcl
resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = lookup(var.instance_types, var.environment, "t3.nano")
  user_data     = templatefile("${path.module}/bootstrap.sh.tftpl", {
    cluster_name = "${var.environment}-cluster"
  })

  tags = merge(
    {
      Name        = "${var.environment}-app"
      Environment = var.environment
    },
    var.extra_tags
  )
}
```

## Your turn

Update the Terraform configuration to dynamic instance parameters and user data:

1. In `userdata.sh.tftpl`, replace the TODO line so the file content is exactly:
```bash
#!/bin/bash
echo "Hello from ${server_name}"
```
(Make sure to keep the trailing newline).

2. In `main.tf`, update the `aws_instance.web` resource:
- Set `instance_type` using `lookup(var.instance_types, var.environment, "t3.nano")`.
- Set `user_data` using `templatefile("${path.module}/userdata.sh.tftpl", { server_name = "${var.environment}-server" })`.
- Set `tags` by calling `merge()` to combine `{ Name = "${var.environment}-web", Environment = var.environment }` with `var.extra_tags`.

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
