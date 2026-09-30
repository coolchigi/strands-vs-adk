# Inspect and modify state with terraform state commands

*CLI Workflow and State*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - Quiz question 1's explanation mislabels its own options. The answer is index 2 (0-based) — 'scheduled for creation' — which is the third option in the list. The explanation then says 'Option 1 is wrong because…' and 'Option 3 describes destruction', using 1-based counting inconsistently. In the...
> - The exercise's only code change between starter and solution is completing the `bucket_ids` for-expression in outputs.tf — a skill taught in a prior lesson, not in this one. The checks enforce only that output and unrelated resource structure; they enforce nothing about the lesson's objectives...
> - question 1's explanation names an option by its position ("Option 1"), and learn.py numbers options from 1. Name it by what it says.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Use terraform state list, state show, and state rm to inspect and remove a tracked resource without editing the state file directly
- Explain why terraform state push is dangerous and what safeguards (lineage, serial) exist

## Where we are

Earlier lessons established that Terraform tracks every resource it manages in the state file, and that the state file is the source of truth Terraform uses to plan changes. The previous lesson explored the state file's raw JSON structure by hand, reading resource addresses, cached attributes, and dependency arrays directly from terraform.tfstate.

## The idea

## Why use state commands instead of editing the file

You should never manually edit the state file; doing so risks unnecessary drift between your Terraform configuration, state, and infrastructure, which could result in resources being destroyed and recreated on the next apply ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). The `terraform state` commands are the safe alternative: use them to modify Terraform state instead of editing the state file directly ([source](https://developer.hashicorp.com/terraform/cli/commands/state)).

The available subcommands are `list`, `mv`, `pull`, `replace-provider`, `rm`, and `show` ([source](https://developer.hashicorp.com/terraform/cli/commands/state)). All of them work with remote state exactly the same way they work with local state ([source](https://developer.hashicorp.com/terraform/cli/commands/state)).

## Inspecting state: list and show

`terraform state list` lists the resource names and local identifiers tracked in the state file, and is useful for finding a specific resource in complex configurations without parsing everything that `terraform show` outputs ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Resources inside modules appear with their module path prefix ([source](https://developer.hashicorp.com/terraform/tutorials/aws/aws-asg)). Because `list` is read-only, it does not write any backup files ([source](https://developer.hashicorp.com/terraform/cli/commands/state)).

`terraform state show ADDRESS` displays the attributes of a single resource in the state file that matches the given address ([source](https://developer.hashicorp.com/terraform/cli/commands/state/show)). The address must point to a single resource in resource addressing format ([source](https://developer.hashicorp.com/terraform/cli/commands/state/show)). A resource created with `count` is addressed with a zero-based index in square brackets, e.g. `aws_subnet.public[0]` ([source](https://developer.hashicorp.com/terraform/cli/commands/state/show)). A resource created with `for_each` is addressed with its instance key in double quotes inside square brackets, e.g. `aws_s3_bucket.env["logs"]` — on Linux/Mac the whole address should be wrapped in single quotes ([source](https://developer.hashicorp.com/terraform/cli/commands/state/show)). Terraform v1.16 added a `-json` flag that produces machine-readable JSON output whose top-level keys are `format_version`, `resource`, and `diagnostics` ([source](https://developer.hashicorp.com/terraform/cli/commands/state/show)) ([source](https://developer.hashicorp.com/terraform/cli/commands/state/show)).

## Removing a resource from state: state rm

`terraform state rm ADDRESS` removes the resource at that address from the state file without destroying the real infrastructure. Because this modifies state, Terraform automatically writes a backup file, and this behaviour cannot be disabled ([source](https://developer.hashicorp.com/terraform/cli/commands/state)). You can control where the backup is written with the `-backup` flag ([source](https://developer.hashicorp.com/terraform/cli/commands/state)); if you no longer need it, you must remove it manually ([source](https://developer.hashicorp.com/terraform/cli/commands/state)).

After a `state rm`, Terraform no longer knows the resource exists. Because the resource is still in your configuration, the next `terraform plan` will show it scheduled for creation ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Running `terraform apply` brings it back under management, making state consistent again ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

## Why terraform state push is dangerous

`terraform state push` manually overwrites remote state and is considered extremely dangerous ([source](https://developer.hashicorp.com/terraform/language/state/backends)). Two safeguards exist: **lineage** (a unique ID assigned when a state file is first created — Terraform refuses to push state whose lineage differs from the remote) and **serial** (a counter incremented on every write — Terraform refuses to push state with a lower serial than the remote, preventing accidental rollbacks). Both protections can be bypassed with the `-force` flag, but making a backup with `terraform state pull` first is always recommended before forcing an overwrite ([source](https://developer.hashicorp.com/terraform/language/state/backends)).

## Worked example

# Worked example: removing and reconciling a tracked resource

Suppose your configuration manages two S3 buckets via `for_each`:

```hcl
resource "aws_s3_bucket" "env" {
  for_each = tomap({
    logs    = "access-logs"
    backups = "nightly-backups"
  })
  bucket = each.key
}
```

After `terraform apply`, the state contains (among other resources):

```
aws_s3_bucket.env["backups"]
aws_s3_bucket.env["logs"]
aws_instance.app
aws_vpc.main
aws_subnet.public[0]
...
```

**Step 1 – List everything Terraform is tracking.**

```
$ terraform state list
aws_instance.app
aws_s3_bucket.env["backups"]
aws_s3_bucket.env["logs"]
aws_subnet.public[0]
aws_subnet.public[1]
aws_subnet.public[2]
aws_vpc.main
```

This confirms every address we care about.

**Step 2 – Inspect a single resource.**

We want to read three attributes from the `logs` bucket:

```
$ terraform state show 'aws_s3_bucket.env["logs"]'
# aws_s3_bucket.env["logs"]:
resource "aws_s3_bucket" "env" {
    bucket                      = "logs"
    id                          = "logs"
    arn                         = "arn:aws:s3:::logs"
    tags = {
      "Project"  = "myproject-dev"
      "Purpose"  = "access-logs"
    }
    ...
}
```

Three attribute values we can read: `bucket = "logs"`, `id = "logs"`, `arn = "arn:aws:s3:::logs"`.

**Step 3 – Remove the bucket from state.**

```
$ terraform state rm 'aws_s3_bucket.env["logs"]'
Removed aws_s3_bucket.env["logs"]
Successfully removed 1 resource instance(s).
```

Terraform writes a `terraform.tfstate.backup` automatically. The real bucket in LocalStack is untouched.

**Step 4 – Plan shows recreation.**

Because `aws_s3_bucket.env["logs"]` is still in `main.tf` but no longer in state, Terraform plans to create it:

```
$ terraform plan
...
  # aws_s3_bucket.env["logs"] will be created
  + resource "aws_s3_bucket" "env" {
      + bucket = "logs"
      ...
    }

Plan: 1 to add, 0 to change, 0 to destroy.
```

This is exactly what we expected: Terraform sees a configuration resource with no matching state entry.

**Step 5 – Apply to reconcile.**

```
$ terraform apply -auto-approve
aws_s3_bucket.env["logs"]: Creating...
aws_s3_bucket.env["logs"]: Creation complete
Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

`terraform state list` now shows all resources again, and `terraform plan` reports *no changes* — state is consistent with configuration and infrastructure.

## Your turn

Starting from a LocalStack-backed configuration that is already applied, you will practise every state inspection and modification skill from this lesson.

1. Run `terraform init` then `terraform apply -auto-approve` to populate state.
2. Run `terraform state list` and confirm you can see all seven resource addresses (two S3 buckets, one instance, one VPC, three subnets).
3. Run `terraform state show 'aws_s3_bucket.env["backups"]'` and note the values of `bucket`, `id`, and at least one tag.
4. Run `terraform state rm 'aws_s3_bucket.env["backups"]'` to remove that bucket from state.
5. Run `terraform plan` and confirm Terraform plans to recreate `aws_s3_bucket.env["backups"]`.
6. Run `terraform apply -auto-approve` to reconcile, then run `terraform plan` again and confirm there are no changes.

The checks will verify your configuration produces all required resources and that your outputs are in place — run them with `terraform test`.

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
