# Read and interpret terraform plan output

*CLI Workflow and State*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - The explanation and quiz both define -/+ as 'Terraform will destroy the resource and then recreate it' (quiz Q1 explanation: 'a destroy-then-recreate cycle'), but every aws_instance.app block in the starter, solution, and worked example carries lifecycle { create_before_destroy = true }, which...

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Run terraform plan and correctly identify every change symbol (+, -, ~, -/+), the forced-replacement attribute, and the plan summary line
- Save a plan to a file with -out and explain when passing a plan file to terraform apply is preferable to running a fresh plan

## Where we are

Earlier lessons built a configuration with an EC2 instance, a VPC, subnets, and S3 buckets, and used `terraform apply` against LocalStack to provision everything. You also learned that Terraform tracks what it manages through a state file, and that variables let you parameterize a configuration without editing `main.tf`.

## The idea

## What terraform plan does

`terraform plan` is one of the three core CLI commands for provisioning tasks, alongside `terraform apply` and `terraform destroy` ([source](https://developer.hashicorp.com/terraform/cli/run)). It evaluates the configuration to determine the desired state of every declared resource, compares that to real infrastructure using state data, and checks current resource state through the provider's API ([source](https://developer.hashicorp.com/terraform/cli/run)). It does **not** make any actual changes to real infrastructure — it only presents a description of the changes needed ([source](https://developer.hashicorp.com/terraform/cli/run)). If no changes are needed at all, `terraform plan` simply reports that no actions need to be taken ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)).

By default, Terraform reads the current remote state, compares it to the configuration, and proposes a set of change actions that would make remote objects match the configuration ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)). The plan subcommand looks in the current working directory for the root module configuration ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)), and like all three core commands, it requires an initialized working directory ([source](https://developer.hashicorp.com/terraform/cli/run)).

## Reading the change symbols

Every resource block in plan output is prefixed with a symbol that tells you what will happen ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)):

| Symbol | Action | Meaning |
|--------|--------|---------|
| `+` | Create | The resource does not exist yet; Terraform will create it |
| `-` | Destroy | Terraform will delete this resource |
| `~` | In-place update | Terraform will update attributes without destroying the resource |
| `-/+` | Replace | Terraform will destroy the resource and then recreate it |

The replace (`-/+`) case deserves special attention. When an attribute that cannot be changed in place is modified, Terraform marks that attribute with `# forces replacement` on the same line ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)). For example, changing the `ami` of a running EC2 instance forces replacement because AWS cannot swap the AMI of an existing instance.

## The plan summary line

At the end of the output, Terraform prints a summary such as:

```
Plan: 2 to add, 1 to change, 2 to destroy.
```

This line counts resources across all three categories ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)). Match it against what you expected before moving on.

## Saving a plan with -out

A plan run without `-out=FILE` produces a *speculative plan* — it describes what would happen but carries no intent to apply ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)). The `-out=FILENAME` option saves the generated plan to a file that can later be passed to `terraform apply` to execute exactly those planned changes ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)). The conventional filename is `tfplan`; you must not use a `.tf` suffix because Terraform would try to parse it as configuration ([source](https://developer.hashicorp.com/terraform/cli/commands/plan)).

Passing a saved plan file to `apply` guarantees that exactly the changes you reviewed are the ones that run — nothing more, nothing less ([source](https://developer.hashicorp.com/terraform/cli/run)). This matters most in CI/CD pipelines and team workflows, where a plan is reviewed and approved first, and then the saved file is applied later. A fresh `apply` (without `-out`) re-runs the plan at apply time, so any infrastructure change that happened between the review and the apply could produce a different set of actions than the one you approved.

## Worked example

## Worked example: spotting every symbol in one plan run

Suppose you have a fresh working directory with no state. Your configuration declares:
- one `aws_vpc.main`
- one `aws_instance.app` using `instance_type = "t3.micro"`

**Step 1 — run the plan and save it**

```
terraform plan -out=tfplan
```

Terraform prints something like:

```
Terraform will perform the following actions:

  # aws_vpc.main will be created
  + resource "aws_vpc" "main" {
      + cidr_block = "10.0.0.0/16"
      + id         = (known after apply)
      ...
    }

  # aws_instance.app will be created
  + resource "aws_instance" "app" {
      + ami           = "ami-0c55b159cbfafe1f0"
      + instance_type = "t3.micro"
      + id            = (known after apply)
      ...
    }

Plan: 2 to add, 0 to change, 0 to destroy.
```

Both blocks carry `+` — create — because the state is empty and neither resource exists yet. The summary says `2 to add`, which matches.

**Step 2 — apply to create state, then change the AMI**

After `terraform apply tfplan`, both resources exist in state. Now change the AMI in `main.tf`:

```hcl
ami = "ami-0abcdef1234567890"   # was ami-0c55b159cbfafe1f0
```

Run `terraform plan -out=tfplan` again:

```
  # aws_instance.app must be replaced
  -/+ resource "aws_instance" "app" {
      ~ ami = "ami-0c55b159cbfafe1f0" -> "ami-0abcdef1234567890" # forces replacement
        instance_type = "t3.micro"
      ...
    }

Plan: 1 to add, 0 to change, 1 to destroy.
```

**Reading the output:**

- The symbol is `-/+` → Terraform will **destroy then recreate** the instance.
- The `ami` line shows the old value → new value and is annotated `# forces replacement`. That is the attribute causing the replace, not an in-place update.
- The summary `1 to add, 0 to change, 1 to destroy` accounts for the destroy and the subsequent create as separate events.
- The `instance_type` line has no symbol prefix — it is not changing.
- The plan file `tfplan` was saved. Running `terraform apply tfplan` would carry out exactly these changes; a fresh `terraform apply` (no file) would re-plan at that moment, potentially picking up any drift that occurred in between.

## Your turn

You have the Unit 2 configuration already initialized and applied against LocalStack (state exists). Your tasks:

1. In `terraform.tfvars`, change `instance_type` from `"t3.micro"` to `"t3.small"`. This is an in-place update (`~`).
2. In `main.tf`, change the `ami` value on `aws_instance.app` from `"ami-0c55b159cbfafe1f0"` to `"ami-0deadbeef00000000"`. This forces replacement (`-/+`).
3. Save the plan with `terraform plan -out=tfplan`.
4. Read every annotated line: confirm the `-/+` symbol appears for `aws_instance.app`, identify the `# forces replacement` attribute (`ami`), and note the plan summary line.
5. Expose the summary counts as outputs so the checks can verify your configuration produces the expected resource set.

Note: `instance_type` is an in-place-updatable attribute, but `ami` forces replacement — so the combined effect on `aws_instance.app` is `-/+`.

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
