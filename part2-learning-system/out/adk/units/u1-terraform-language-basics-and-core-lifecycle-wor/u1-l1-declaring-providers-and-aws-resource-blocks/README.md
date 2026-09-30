# Declaring Providers and AWS Resource Blocks

*Terraform Language Basics and Core Lifecycle Workflow*

## By the end of this lesson you can

- Configure the AWS provider and version constraints inside a required_providers block pointing to local mock endpoints
- Declare AWS resource blocks with required type labels, resource names, and arguments

## Where we are

Terraform manages cloud infrastructure through declarative configuration files that represent cloud resources. While you already understand AWS concepts like VPCs and S3 buckets, Terraform automates their provisioning using specialized plugins called providers. In this foundational lesson, you will establish your first provider configuration and declare managed resources.

## The idea

Provider requirements are declared within a `required_providers` block nested inside the top-level `terraform` configuration block ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)). In a `required_providers` block, each provider entry specifies a local name as the key and an object with `source` and `version` arguments as the value ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)). Outside of the `required_providers` block, Terraform configurations reference providers by their assigned local names ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)).

A provider source address consists of three slash-delimited components: an optional hostname, a namespace, and a type ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)). When the hostname is omitted from a provider source address, Terraform defaults to the public registry at `registry.terraform.io` ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)). If a provider requirement omits the `source` argument, Terraform uses an implied source address of `registry.terraform.io/hashicorp/<LOCAL NAME>` ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)). The `version` argument in a provider requirement is optional, and omitting it causes Terraform to accept any available version of the provider ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)). The `~>` version constraint operator allows only the rightmost component of the specified version number to increment ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)).

The `provider` block is used to declare and configure Terraform plugins called providers ([source](https://developer.hashicorp.com/terraform/language/block/provider)). The `provider` block accepts provider-specific arguments, an `alias` argument, and a deprecated `version` argument ([source](https://developer.hashicorp.com/terraform/language/block/provider)). The `version` argument inside a `provider` block is deprecated; provider version constraints should instead be declared in the `required_providers` block inside the `terraform` block ([source](https://developer.hashicorp.com/terraform/language/block/provider)). If a `provider` block is not explicitly defined, Terraform assumes and creates an empty default configuration for that provider ([source](https://developer.hashicorp.com/terraform/language/block/provider)). However, Terraform raises an error if a provider has required arguments but only an empty default configuration is created ([source](https://developer.hashicorp.com/terraform/language/block/provider)).

The `alias` argument allows defining multiple configurations for the same provider, enabling different configurations to be used by individual resources, data sources, or modules ([source](https://developer.hashicorp.com/terraform/language/block/provider)). To create multiple configurations for a provider, declare multiple `provider` blocks with the same name and add the `alias` argument to each additional configuration ([source](https://developer.hashicorp.com/terraform/language/block/provider)). To refer to an aliased provider configuration within resource, data, or module blocks, use the format `<PROVIDER_NAME>.<ALIAS>` in the `provider` argument ([source](https://developer.hashicorp.com/terraform/language/block/provider)). When multiple configurations exist for a provider, the block without an alias is the default configuration, and resources without a `provider` meta-argument will use it ([source](https://developer.hashicorp.com/terraform/language/block/provider)). If every provider block in a configuration includes an alias, Terraform creates an implied empty default configuration for that provider ([source](https://developer.hashicorp.com/terraform/language/block/provider)). The `provider` meta-argument within a resource block allows a resource to select an alternate provider configuration by referencing its alias ([source](https://developer.hashicorp.com/terraform/language/block/resource)).

When a resource does not explicitly define which provider configuration to use, Terraform determines the local provider name from the first word of the resource type ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)). The resource label is used by Terraform to track the resource in state and does not influence settings on the actual infrastructure resource ([source](https://developer.hashicorp.com/terraform/language/block/resource)). To reference a resource in a Terraform configuration, you reference it using `<TYPE>.<LABEL>` syntax ([source](https://developer.hashicorp.com/terraform/language/block/resource)). Managed resources are referenced using the resource type and resource name in the format `<RESOURCE TYPE>.<NAME>` ([source](https://developer.hashicorp.com/terraform/language/expressions/references)).

## Worked example

### Step 1: Declaring provider requirements

To use the AWS provider, declare it inside the `terraform` configuration block using `required_providers`. We specify the source registry address and restrict the version using `~> 6.0`:

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

### Step 2: Configuring the provider

Next, configure the provider settings in a `provider` block using the local name `aws`. For local testing without a live AWS account, configure endpoint routing to a local mock address:

```hcl
provider "aws" {
  region                      = "us-east-1"
  skip_credentials_validation = true
  skip_requesting_account_id  = true

  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
  }
}
```

### Step 3: Declaring an AWS managed resource

Now declare an AWS resource using the `resource` keyword, followed by the resource type (`aws_vpc`) and a local name (`network`). Because `aws_vpc` begins with `aws`, Terraform automatically associates it with our default `aws` provider configuration:

```hcl
resource "aws_vpc" "network" {
  cidr_block = "10.10.0.0/16"
}
```

In this block:
- `aws_vpc` specifies the managed resource type.
- `network` is the local resource label used to track this resource in Terraform state and reference it as `aws_vpc.network`.
- `cidr_block` is the provider-specific configuration argument.

## Your turn

In `main.tf`, the `terraform` block and `provider "aws"` block are already configured for you. Complete the configuration by declaring two managed resources:
1. An `aws_vpc` resource with the local name `"main"` and argument `cidr_block = "10.0.0.0/16"`.
2. An `aws_s3_bucket` resource with the local name `"data"` and argument `bucket = "my-learning-bucket-2024"`.

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
