# Working Directory Initialization and Configuration Validation

*Terraform Language Basics and Core Lifecycle Workflow*

## By the end of this lesson you can

- Initialize a working directory using terraform init to download provider plugins into the .terraform cache
- Validate HCL syntax and enforce standard formatting using terraform validate and terraform fmt

## Where we are

In earlier lessons, we learned how to declare provider requirements and define infrastructure resources such as VPCs, subnets, and internet gateways using HashiCorp Configuration Language (HCL). We also explored how implicit and explicit dependencies connect these resources together.

## The idea

Before Terraform can carry out operations such as provisioning infrastructure or updating state, the working directory must be initialized ([source](https://developer.hashicorp.com/terraform/cli/init)). Running `terraform init` initializes a working directory containing Terraform configuration, enabling subsequent commands such as `terraform plan` and `terraform apply` ([source](https://developer.hashicorp.com/terraform/cli/init)). The `terraform init` command is used to initialize Terraform and initialize provider plugins ([source](https://developer.hashicorp.com/terraform/intro/core-workflow)). During initialization, Terraform downloads and installs provider plugins, downloads modules, and accesses state in the configured backend ([source](https://developer.hashicorp.com/terraform/cli/init)). Basic provisioning commands such as `terraform plan`, `terraform apply`, and `terraform destroy` all require an initialized working directory ([source](https://developer.hashicorp.com/terraform/cli/run)). If you attempt to execute commands that require initialization without running init first, the command fails with an error specifying that init must be run ([source](https://developer.hashicorp.com/terraform/cli/init)).

During initialization, Terraform creates a hidden `.terraform` directory ([source](https://developer.hashicorp.com/terraform/cli/init)). This directory stores cached provider plugins, modules, the active workspace, and backend configuration ([source](https://developer.hashicorp.com/terraform/cli/init)). The `terraform init` command is idempotent, meaning running it again when no changes are needed has no effect ([source](https://developer.hashicorp.com/terraform/cli/init)). However, changes to backend configurations, provider requirements, or module sources and version constraints require reinitialization before normal operations can continue ([source](https://developer.hashicorp.com/terraform/cli/init)). While `terraform get` downloads referenced modules without performing other initialization tasks, it does not download provider plugins or configure backends ([source](https://developer.hashicorp.com/terraform/cli/init)).

The `terraform validate` command checks the syntax and arguments of configuration files in a directory, including resource and module argument and attribute names and types ([source](https://developer.hashicorp.com/terraform/cli/code)). In addition, `terraform plan` and `terraform apply` automatically validate the configuration before carrying out any other tasks ([source](https://developer.hashicorp.com/terraform/cli/code)). To maintain clean and consistent code, the `terraform fmt` command automatically rewrites Terraform configuration files into a canonical format and style ([source](https://developer.hashicorp.com/terraform/cli/code)).

## Worked example

Consider starting a new project directory with an unformatted `main.tf` file:

```hcl
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

resource "aws_vpc" "app" {
  cidr_block = "10.1.0.0/16"
  enable_dns_support = true
}
```

1. **Initialize the working directory**:
   Run `terraform init` in your terminal. Terraform inspects `required_providers`, identifies `hashicorp/aws`, and downloads the matching provider binary into the local `.terraform/providers/` directory.

2. **Catch syntax or attribute errors early**:
   Suppose an attribute was mistyped as `invalid_cidr = "10.1.0.0/16"`. Running `terraform validate` reads the provider schema cached in `.terraform` and immediately reports an error explaining that argument `invalid_cidr` is not expected on `aws_vpc`.

3. **Enforce canonical formatting**:
   Once the argument name is corrected, running `terraform fmt` scans `.terraform` configuration files in the directory and rewrites them so that assignments and arguments are cleanly aligned according to Terraform's canonical style.

## Your turn

In `main.tf`, update the `aws_subnet.private` resource so that its `cidr_block` is set to `"10.0.2.0/24"` instead of the placeholder `"10.0.99.0/24"`. Run `terraform init` to ensure your provider cache is present, verify syntax with `terraform validate`, format the file canonically with `terraform fmt`, and run `terraform test` to ensure all tests pass.

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
