# AWS Infrastructure Automation with Terraform

Master HashiCorp Terraform from the ground up by building, parameterizing, and modularizing a complete AWS VPC, compute, and storage infrastructure stack. Learn core HCL syntax, provider configurations, dependency modeling, and module architecture, while executing the full Terraform lifecycle against local zero-cost LocalStack endpoints to generate and manipulate real state safely.

## Who this is for

```text
Subject: Terraform (tool)
Goal: deeply understand Terraform and build projects along the way
Starting from: Knows AWS well, but has never written Terraform
Wants to be able to: Build a VPC, compute and storage stack on AWS, organised into modules
Constraints: Do not want to spend money on a cloud account while learning
```

## What you'll be able to do

- Author declarative Terraform configurations defining AWS networking, compute, and storage resources
- Configure provider version constraints, registries, and aliased provider configurations
- Model explicit and implicit infrastructure dependencies using attribute references and graph ordering
- Execute the core Terraform workflow (init, fmt, validate, plan, apply, destroy) without incurring cloud provider costs using LocalStack
- Parameterize infrastructure using typed input variables, precedence rules, custom validation, and built-in functions
- Design and publish reusable root and child module architectures following HashiCorp standard module structure
- Inspect, modify, and migrate Terraform state safely using CLI show, output, and state commands

Written against Terraform 1.16.4 ([source](https://developer.hashicorp.com/terraform/install)).

What this course covers comes from the official documentation, shaped by what you said you want to do. Every fact in a lesson links to the page it came from. `SOURCES.md` lists them all.

## How to use it

```bash
learn next      # where you are, and what's next
learn check     # run the current exercise's tests
learn hint      # one hint at a time
learn quiz      # answer, then see the answers
learn review    # questions you missed, when they're due again
```

No `learn` command? Type `python3 learn.py` wherever it says `learn` (`py learn.py` on Windows), and everything works the same from this folder. Each lesson's exercise says what you need installed to run its tests.

## Known problems

What our own checks and reviewers still found after every retry. Lessons with a problem say so at the top.

- u2-l1: 'Predict variable value assignment according to Terraform precedence rules across CLI flags, tfvars, and environment variables' asks the learner to analyze, and a quiz can't show that. It needs an exercise.

## Units

### u1. Terraform Language Basics and Core Lifecycle Workflow

1. [Declaring Providers and AWS Resource Blocks](units/u1-terraform-language-basics-and-core-lifecycle-wor/u1-l1-declaring-providers-and-aws-resource-blocks/README.md)
2. [Resource Attribute References and Dependency Management](units/u1-terraform-language-basics-and-core-lifecycle-wor/u1-l2-resource-attribute-references-and-dependency-man/README.md)
3. [Working Directory Initialization and Configuration Validation](units/u1-terraform-language-basics-and-core-lifecycle-wor/u1-l3-working-directory-initialization-and-configurati/README.md)
4. [Planning, Applying, and Destroying Infrastructure](units/u1-terraform-language-basics-and-core-lifecycle-wor/u1-l4-planning-applying-and-destroying-infrastructure/README.md)

**Project:** Build an initial network skeleton in a single configuration file containing an AWS provider with mock LocalStack endpoints, an aws_vpc, an aws_internet_gateway, and two public aws_subnets cross-referencing the VPC ID. Initialize the directory, run validate and fmt, generate a speculative plan to disk, apply the plan against LocalStack to verify that terraform.tfstate is generated, and confirm infrastructure integrity.

### u2. Parameterization, Expressions, and Outputs

1. [Input Variables and Precedence Resolution](units/u2-parameterization-expressions-and-outputs/u2-l1-input-variables-and-precedence-resolution/README.md)
2. [HCL Operators, Functions, and Dynamic Expressions](units/u2-parameterization-expressions-and-outputs/u2-l2-hcl-operators-functions-and-dynamic-expressions/README.md)
3. [Exposing State and Resource Attributes with Output Values](units/u2-parameterization-expressions-and-outputs/u2-l3-exposing-state-and-resource-attributes-with-outp/README.md)

**Project:** Refactor the AWS network configuration into separate `variables.tf`, `main.tf`, and `outputs.tf` files. Parameterize VPC CIDR, subnet CIDR maps, and availability zones using validation rules. Use `merge()` to assign standardized resource tags, and export the VPC ID, public subnet IDs list, and an ephemeral session token in `outputs.tf`. Apply the configuration against LocalStack and confirm outputs print as expected.

### u3. Modular Infrastructure Architecture

1. [Standard Module Architecture and Hierarchy](units/u3-modular-infrastructure-architecture/u3-l1-standard-module-architecture-and-hierarchy/README.md)
2. [Calling Modules from Local and External Sources](units/u3-modular-infrastructure-architecture/u3-l2-calling-modules-from-local-and-external-sources/README.md)
3. [Inter-Module Data Flow and Multi-Instance Scaling](units/u3-modular-infrastructure-architecture/u3-l3-inter-module-data-flow-and-multi-instance-scalin/README.md)

**Project:** Design a complete modular AWS infrastructure repository consisting of a root module and three child modules in `modules/`: `vpc` (network and subnets), `compute` (EC2 instance and security group), and `storage` (S3 bucket with versioning). Wire the outputs of `vpc` as inputs to `compute`. Initialize and apply the entire multi-module stack against LocalStack to verify that all resources are created and wired together in state without incurring any cloud costs.

### u4. State Inspection, Management, and Refactoring

1. [Inspecting State and Output Extraction](units/u4-state-inspection-management-and-refactoring/u4-l1-inspecting-state-and-output-extraction/README.md)
2. [Modifying State Bindings and Refactoring Resources](units/u4-state-inspection-management-and-refactoring/u4-l2-modifying-state-bindings-and-refactoring-resourc/README.md)

**Project:** Perform a zero-downtime state migration on the multi-module AWS stack. Use `terraform state list` to catalog current addresses. Move a standalone S3 storage resource into the child module `module.storage` using `terraform state mv`, verifying state backups are created automatically. Run `terraform plan` to confirm zero resources will be destroyed or recreated, and extract the final state snapshot using `terraform show -json`.
