# Calling Modules from Local and External Sources

*Modular Infrastructure Architecture*

## By the end of this lesson you can

- Declare module blocks referencing local relative file paths and external Git or Registry sources
- Initialize module dependencies using terraform init and terraform get

## Where we are

In the previous lesson, we encapsulated VPC network resources into reusable child module files inside the `modules/vpc` directory. We defined child module inputs with `variable` blocks and exposed resource attributes like the VPC and subnet identifiers using `output` blocks.

## The idea

Terraform retrieves modules from multiple supported sources, including the local file system, the public or private Terraform registry, VCS repositories, object storage, and S3 buckets ([source](https://developer.hashicorp.com/terraform/language/modules), [source](https://developer.hashicorp.com/terraform/language/modules/configuration)). You call modules published to any of these supported sources by declaring a `module` block in your configuration ([source](https://developer.hashicorp.com/terraform/language/modules)). Every `module` block requires a `source` argument, which instructs Terraform where to retrieve the child module's configuration files ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)).

When a root module calls nested child modules stored in the same repository, it should reference them with local relative paths such as `./modules/vpc` or `./modules/consul-cluster` so Terraform considers them part of the same package rather than downloading them separately ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)). However, module blocks within an `examples/` directory should set their source argument to the address an external caller would use rather than a relative path ([source](https://developer.hashicorp.com/terraform/language/modules/develop/structure)).

When calling modules from a Terraform registry, you can define a version constraint using the `version` argument ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). For Git repositories, Terraform by default clones and uses the default branch pointed to by HEAD ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). To target a specific branch, tag, or SHA-1 hash, append the `ref` query parameter to the source URL ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). You can also append the `depth` query parameter to instruct Git to perform a shallow clone containing only the specified number of commits ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)).

After configuring a `module` block in the calling module, running `terraform init` downloads the child module files into a local workspace directory ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)). If you change a module's `source` argument or modify the `version` argument for a registry module, you must rerun `terraform init` to update it ([source](https://developer.hashicorp.com/terraform/language/modules/configuration)).

## Worked example

Consider a project that needs a local VPC module and an external security group module.

First, reference the local child module using a relative file path starting with `./`:
```hcl
module "vpc" {
  source             = "./modules/vpc"
  vpc_cidr           = "10.0.0.0/16"
  public_subnet_cidr = "10.0.1.0/24"
}
```
Because `./modules/vpc` is a relative local path, Terraform recognizes it as part of the local workspace package and reads the files directly from the directory without a remote download.

Next, if we need an external module from Git pinned to a specific release tag with a shallow clone, we specify the Git source URL with `ref` and `depth` query parameters:
```hcl
module "app_cluster" {
  source = "git::https://example.com/infra/app-cluster.git?ref=v1.2.0&depth=1"
  vpc_id = module.vpc.vpc_id
}
```

Finally, run `terraform init`. Terraform parses the configuration, identifies the module blocks, reads the local module from `./modules/vpc`, and clones the Git repository into the `.terraform/modules` directory. If we later update `ref=v1.2.0` to `ref=v1.3.0`, running `terraform init` again fetches the updated version into the local workspace.

## Your turn

In `main.tf`, wire the local `module "vpc"` block using the relative source path `./modules/vpc`. Pass the root variables `var.vpc_cidr` and `var.public_subnet_cidr` into the module's `vpc_cidr` and `public_subnet_cidr` arguments. Then wire the `aws_instance.web` resource's `subnet_id` argument to the module's `public_subnet_id` output (`module.vpc.public_subnet_id`).

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
