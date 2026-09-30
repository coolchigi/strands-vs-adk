# Terraform Deep Dive: VPC, Compute & Storage on AWS (LocalStack)

A 16-lesson, 5-unit curriculum for an AWS-fluent engineer who has never written Terraform. The learner builds a single growing project — a modular VPC + compute + storage stack — from scratch. All exercises run against LocalStack so zero cloud spend is incurred. Each unit closes with an unguided project that forces the learner to apply the unit's capabilities without step-by-step guidance.

## Who this is for

```text
Subject: Terraform (tool)
Goal: Deeply understand Terraform and build projects along the way.
Starting from: Knows AWS well but has never written Terraform.
Wants to be able to: Build a VPC, compute and storage stack on AWS, organised into modules.
Constraints: No spending money on a cloud account while learning
```

## What you'll be able to do

- Install and configure Terraform with LocalStack so all exercises run without cloud spend
- Read and write idiomatic HCL including variables, locals, outputs, expressions, and meta-arguments
- Execute the full terraform init → plan → apply → destroy lifecycle and explain what each step does to state
- Inspect and reason about the state file using terraform state subcommands without editing it directly
- Compose a multi-module Terraform project where child modules communicate through inputs and outputs
- Build and apply a complete, module-organised VPC + EC2 + S3 stack on LocalStack, verify it with the AWS CLI, and destroy it cleanly

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

- The no-cost constraint is central to the entire course, yet the LocalStack coverage is thin and fragmented. There are only a handful of community claims about LocalStack setup (17f02b37986f, 8fe6f15a6dfd, 62feb8cb180c, c7e1835bd5e9, 4473733813a2, 0f83957879a4, df0001214c65, bfb33a4c2dd4,...
- The research covers AWS credential setup (environment variables, aws configure list) but provides no evidence for how to use a named AWS profile with zero permissions — or a wholly offline approach — as a fallback when LocalStack is not used. Claim 35523dedfe0a covers env-var credentials and...
- Objective 6.5 requires the learner to 'apply the full stack, verify resources in the AWS console or CLI, and then destroy it cleanly to avoid charges.' The research for 6.5 is almost entirely AWS CLI verification commands (describe-vpcs, describe-instances, aws s3 ls, attach-volume,...
- The storage module objective (6.3) covers only S3 buckets and EBS volumes in the objective text, but the evidence is almost exclusively S3-focused (9e7e72529870, dc1057332182, 8981f5b8c2b6, 33c98b8eb05c, e3b8364afeab, aa78fa16da83). EBS volume provisioning with Terraform — the aws_ebs_volume...
- Objective 6.2 mentions both 'EC2 instances' and 'an Auto Scaling group' as alternatives. The research covers both (aws_autoscaling_group, aws_launch_configuration, etc.), but there is no evidence for the aws_instance resource used in a subnet with a security group in the context of the networking...
- Objective 6.1 requires creating a VPC, subnets across AZs, an internet gateway, and route tables. The research covers VPC and subnets (bbd3e82263cd, 1b691718e1b9, ac3a1b79c464) and cidrsubnet (7c5bab182a5a, bbd3e82263cd, etc.), but there is no evidence for the aws_route_table,...
- Similarly, the aws_internet_gateway Terraform resource block is not evidenced. Claim 4e5a1c6e7b32 covers the AWS CLI command to attach an internet gateway, and 71ee1c9fc574 mentions a for_each pattern for internet gateways abstractly, but there are no claims showing the aws_internet_gateway...
- Claim 44893735e3d1 states Terraform does not automatically roll back a partially-completed apply. This is important safety knowledge for a learner, and it is covered. However, there is no evidence for what a learner should actually do to recover from a partial apply (e.g. re-running apply, using...
- Claim 41e06686373e asserts HashiCorp maintains compatibility between Terraform versions so a configuration written for one version works with any later minor version. This is mapped to objective 1.1 (install Terraform). The claim is about version compatibility policy, not installation, and the...
- u2-l1: 'Predict the effect of create_before_destroy and ignore_changes lifecycle arguments on a planned replacement' asks the learner to analyze, and a quiz can't show that. It needs an exercise.
- u2-l2: 'Choose between -var flag, .tfvars file, and TF_VAR_ environment variable to supply a value, explaining the precedence order' asks the learner to analyze, and a quiz can't show that. It needs an exercise.
- u2-l5: 'Predict the CIDR output of a cidrsubnet call given a parent prefix, newbits, and netnum' asks the learner to analyze, and a quiz can't show that. It needs an exercise.
- u2-l6: 'Choose between count and for_each for a given scenario, justifying the decision' asks the learner to evaluate, and a quiz can't show that. It needs an exercise.
- u2-l6 teaches from claims we don't have: ['24c0b2e968051']
- u1-l1: The exercise check can be passed without ever installing Terraform. The hints give the exact example string "Terraform v1.16.4", the worked example prints the same string, and the solution file hardcodes it. A learner who simply copies that string into the local value will satisfy both...
- u1-l2: the untouched starter already passes the checks, so there is nothing to do
- u1-l3: the checks don't test the gap at provider.tf line 2: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.
- u1-l3: the checks don't test the gap at provider.tf line 7: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.
- u1-l3: the checks don't test the gap at provider.tf line 10: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.
- u1-l4: The explanation says `terraform init -upgrade` 'ignores the lock file' — but the citation only supports that it pulls the newest version satisfying the constraint and updates the lock file. 'Ignores' overstates it: Terraform still writes a new lock file entry afterward. This same...
- u1-l4: The exercise asks the learner to record the same value ('registry.terraform.io/hashicorp/aws') in two separate locals (lock_provider_source and provider_install_dir), and both checks test for the identical string. There is no meaningful second objective being practised: a learner who guesses...
- u1-l4: The lesson's stated objective includes describing what the .terraform *directory* contains (the versioned, platform-specific binary path), but the exercise checks only the three-segment source-address prefix — not the version segment, the platform segment, or any evidence that the learner...
- u2-l1: The exercise task explicitly requires a lifecycle block with `create_before_destroy = true`, and the solution includes it, but none of the three checks assert anything about the lifecycle block. A learner can omit it entirely and still pass all checks. The check for the exercise's stated...
- u2-l1: All three quiz questions target the single objective 'Predict the effect of create_before_destroy and ignore_changes lifecycle arguments on a planned replacement'. There is no quiz question covering the other practised skill — writing a resource block with the correct labels and required...
- u2-l1: The claim that `create_before_destroy = true` provisions the replacement before tearing down the original is cited as `c:5173ec833c69` in the explanation but as `c:95861c25bb7a` in the worked example (Step 3). These are different citation IDs for the same factual claim; one of them is...
- u2-l2: The Precedence section ranks -var > .tfvars > default but never states where TF_VAR_ sits in that order. The stated objective is to explain the full precedence order, and environment variables are listed as one of the three supply methods, so the omission leaves the explanation short of what...
- u2-l2: No quiz question tests where TF_VAR_ falls in the precedence order. Q2 tests undeclared-variable behaviour (silent ignore), which is a different property. The objective explicitly includes 'explaining the precedence order' for all three supply methods, so a question distinguishing TF_VAR_...
- u2-l3: Quiz question 3's answer explanation introduces citation [c:88aaa7742c62] — 'A local value can reference another local value using the local.<NAME> syntax [c:88aaa7742c62]' — but this citation identifier does not appear anywhere else in the lesson and has no corresponding checked claim. The...
- u2-l3: Quiz question 1's answer explanation asserts 'locals and variables are both resolved during the same evaluation pass' as a rebuttal to distractor B. No citation in the lesson covers Terraform's evaluation ordering. This claim goes beyond what any cited source in the lesson says, violating...
- u2-l4: The check for app_secret uses `nonsensitive(output.app_secret) == "s3cr3t-token-abc123"`, which passes whether or not `sensitive = true` is present. A learner who omits `sensitive = true` still passes the check, because `nonsensitive()` on an already-non-sensitive value is valid HCL and...
- u2-l5: The worked example's Step 3 locals block uses `var.project` and `var.environment` (in `name_prefix`) but Step 1 only declares `vpc_cidr` and `availability_zones`. A learner following the worked example in isolation has a broken configuration — those two variables are never declared in the...
- u2-l5: The `subnet_count_local_uses_length` check is a tautology: it asserts `local.subnet_count == length(var.availability_zones)`. Because `var.availability_zones` defaults to a three-element list, a learner who hardcodes `subnet_count = 3` passes this check just as easily as one who writes...
- u2-l6: the checks don't test the gap at main.tf line 43: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.
- u3-l1: The explanation and quiz both define -/+ as 'Terraform will destroy the resource and then recreate it' (quiz Q1 explanation: 'a destroy-then-recreate cycle'), but every aws_instance.app block in the starter, solution, and worked example carries lifecycle { create_before_destroy = true },...
- u3-l2: In the worked example, citation c:27202231642d is used to support two distinct claims: (1) that outputs are displayed after apply, and (2) that sensitive outputs appear as `<sensitive>` in the terminal. In the explanation section, c:27202231642d is cited only for claim (1). If the source...
- u3-l2: The lesson title and all three objectives centre on `terraform apply` and `terraform destroy`, but the only hands-on work the learner actually authors in the exercise is declaring two output blocks in `outputs.tf`. Writing output declarations was the subject of the previous lesson; it is not...
- u3-l3: the untouched starter already passes the checks, so there is nothing to do
- u3-l4: Quiz question 1's explanation mislabels its own options. The answer is index 2 (0-based) — 'scheduled for creation' — which is the third option in the list. The explanation then says 'Option 1 is wrong because…' and 'Option 3 describes destruction', using 1-based counting inconsistently. In...
- u3-l4: The exercise's only code change between starter and solution is completing the `bucket_ids` for-expression in outputs.tf — a skill taught in a prior lesson, not in this one. The checks enforce only that output and unrelated resource structure; they enforce nothing about the lesson's...
- u3-l5: the exercise has no .tftest.hcl checks
- u3-l6: the untouched starter already passes the checks, so there is nothing to do
- u4-l1: Quiz question 3, option D reads "Any file works equally well; the three standard filenames have no special meaning to Terraform." The lesson's own quiz explanation concedes "Terraform itself does not enforce the convention," and the explanation text nowhere claims Terraform enforces the...
- u4-l2: the checks don't test the gap at modules/compute/main.tf line 4: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.
- u4-l3: the solution does not pass its own checks: tests/for_each_module.tftest.hcl... in progress run "two_storage_instances_exist"... pass run "storage_instances_have_distinct_bucket_names"... pass run "outputs_reference_correct_instances"... fail tests/for_each_module.tftest.hcl... tearing down...
- u5-l1: the starter is not valid Terraform, so the learner would see a syntax error instead of a failing test: Error: Unsupported argument on main.tf line 4, in module "networking": 4: vpc_cidr = "10.0.0.0/16" An argument named "vpc_cidr" is not expected here. Error: Unsupported argument on main.tf...
- u5-l2: the exercise has no .tftest.hcl checks
- u5-l3: the starter is not valid Terraform, so the learner would see a syntax error instead of a failing test: Error: Unsupported argument on main.tf line 19, in module "storage": 19: bucket_name = each.key An argument named "bucket_name" is not expected here.
- u5-l4: Quiz Q1 option C (adding depends_on inside an output block) is not valid Terraform syntax. No learner who has worked through the lesson would hold this misconception, so it does not function as a plausible distractor. Replace it with a wrong answer a learner might genuinely reach for, such...
- u5-l4: Quiz Q2 says the teammate runs terraform output inside the modules/networking directory. That directory has no state file and no initialised working directory, so the command would error on a missing backend rather than silently show nothing. The stem conflates two different problems (no...
- u1-l2: question 1's explanation names an option by its position ("option 3"), and learn.py numbers options from 1. Name it by what it says.
- u1-l2: question 2's explanation names an option by its position ("Option 1"), and learn.py numbers options from 1. Name it by what it says.
- u1-l2: question 3's explanation names an option by its position ("option 1)"), and learn.py numbers options from 1. Name it by what it says.
- u1-l4: question 1's explanation names an option by its position ("Option 0"), and learn.py numbers options from 1. Name it by what it says.
- u2-l3: question 1's explanation names an option by its position ("Option B"), and learn.py numbers options from 1. Name it by what it says.
- u2-l3: question 3's explanation names an option by its position ("Option B"), and learn.py numbers options from 1. Name it by what it says.
- u2-l5: question 1's explanation names an option by its position ("Option A"), and learn.py numbers options from 1. Name it by what it says.
- u2-l5: question 3's explanation names an option by its position ("Option A"), and learn.py numbers options from 1. Name it by what it says.
- u3-l4: question 1's explanation names an option by its position ("Option 1"), and learn.py numbers options from 1. Name it by what it says.

## Units

### u1. Install, Configure & Initialise

1. [Install Terraform CLI and verify the installation](units/u1-install-configure-initialise/u1-l1-install-terraform-cli-and-verify-the-installatio/README.md)
2. [Declare required_providers and pin the AWS provider version](units/u1-install-configure-initialise/u1-l2-declare-required-providers-and-pin-the-aws-provi/README.md)
3. [Configure the AWS provider to target LocalStack](units/u1-install-configure-initialise/u1-l3-configure-the-aws-provider-to-target-localstack/README.md)
4. [Initialise the working directory with terraform init](units/u1-install-configure-initialise/u1-l4-initialise-the-working-directory-with-terraform-/README.md)

**Project:** Starting from an empty directory, create a complete Terraform configuration (terraform.tf + main.tf) that targets LocalStack, pins the hashicorp/aws provider to ~> 5.0, and initialises cleanly. Verify with terraform -version and terraform init; confirm the .terraform directory and .terraform.lock.hcl exist and contain the expected provider version. No resources need to be declared yet.

### u2. HashiCorp Configuration Language (HCL)

1. [Write resource blocks with arguments and meta-arguments](units/u2-hashicorp-configuration-language-hcl/u2-l1-write-resource-blocks-with-arguments-and-meta-ar/README.md)
2. [Parameterise with input variables](units/u2-hashicorp-configuration-language-hcl/u2-l2-parameterise-with-input-variables/README.md)
3. [Reduce repetition with local values](units/u2-hashicorp-configuration-language-hcl/u2-l3-reduce-repetition-with-local-values/README.md)
4. [Expose values with output blocks](units/u2-hashicorp-configuration-language-hcl/u2-l4-expose-values-with-output-blocks/README.md)
5. [Reference attributes across blocks and use built-in functions](units/u2-hashicorp-configuration-language-hcl/u2-l5-reference-attributes-across-blocks-and-use-built/README.md)
6. [Create multiple resources with count and for_each](units/u2-hashicorp-configuration-language-hcl/u2-l6-create-multiple-resources-with-count-and-for-eac/README.md)

**Project:** Extend the project directory: declare an S3 bucket resource and an EC2 instance resource (both targeting LocalStack). Use at least one input variable for the bucket name and instance type, at least one local value for a shared name-prefix tag, and output the bucket's id and the instance's id. Use count or for_each to create two subnets from a CIDR variable using cidrsubnet. Apply to LocalStack and verify the outputs print correctly.

### u3. CLI Workflow and State

1. [Read and interpret terraform plan output](units/u3-cli-workflow-and-state/u3-l1-read-and-interpret-terraform-plan-output/README.md)
2. [Apply and destroy infrastructure](units/u3-cli-workflow-and-state/u3-l2-apply-and-destroy-infrastructure/README.md)
3. [Understand the state file](units/u3-cli-workflow-and-state/u3-l3-understand-the-state-file/README.md)
4. [Inspect and modify state with terraform state commands](units/u3-cli-workflow-and-state/u3-l4-inspect-and-modify-state-with-terraform-state-co/README.md)
5. [Remote state: risks, backends, and locking](units/u3-cli-workflow-and-state/u3-l5-remote-state-risks-backends-and-locking/README.md)
6. [Reinitialise after dependency changes](units/u3-cli-workflow-and-state/u3-l6-reinitialise-after-dependency-changes/README.md)

**Project:** Using the configuration built in Unit 2, run the full workflow: terraform plan -out=tfplan (read and annotate the plan output), terraform apply tfplan (confirm state file is updated), terraform state list and terraform state show for two resources, terraform state rm one resource and observe the next plan, then terraform destroy. Write a short explanation of what the state file contains and why it must not be committed to version control.

### u4. Reusable Modules

1. [Structure a project as root and child modules](units/u4-reusable-modules/u4-l1-structure-a-project-as-root-and-child-modules/README.md)
2. [Write child module inputs and outputs](units/u4-reusable-modules/u4-l2-write-child-module-inputs-and-outputs/README.md)
3. [Call a module multiple times with different inputs](units/u4-reusable-modules/u4-l3-call-a-module-multiple-times-with-different-inpu/README.md)

**Project:** Refactor the Unit 2/3 configuration into three child modules under a modules/ directory: modules/storage (S3 bucket), modules/compute (EC2 instance), and modules/network (subnets). Each module must have variables.tf, main.tf, and outputs.tf. The root module's main.tf calls all three, threading the subnet IDs from the network module into the compute module. Run terraform init, plan, and apply against LocalStack and verify all resources are created. Then call the storage module a second time with a different bucket name.

### u5. Full VPC, Compute & Storage Stack

1. [Write the networking module](units/u5-full-vpc-compute-storage-stack/u5-l1-write-the-networking-module/README.md)
2. [Write the compute module](units/u5-full-vpc-compute-storage-stack/u5-l2-write-the-compute-module/README.md)
3. [Write the storage module](units/u5-full-vpc-compute-storage-stack/u5-l3-write-the-storage-module/README.md)
4. [Compose all three modules and verify the full stack](units/u5-full-vpc-compute-storage-stack/u5-l4-compose-all-three-modules-and-verify-the-full-st/README.md)

**Project:** This unit's project IS the capstone: apply the complete root module (networking + compute + storage) to LocalStack, then verify every created resource using AWS CLI commands (describe-vpcs, describe-instances, s3 ls), inspect two resources with terraform state show, and finally run terraform destroy and confirm an empty state file. The project is complete when: all three modules apply without error, CLI verification shows the correct VPC CIDR and instance placement, and the state file is empty after destroy.
