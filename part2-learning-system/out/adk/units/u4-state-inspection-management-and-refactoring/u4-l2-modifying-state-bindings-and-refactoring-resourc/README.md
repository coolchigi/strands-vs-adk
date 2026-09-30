# Modifying State Bindings and Refactoring Resources

*State Inspection, Management, and Refactoring*

## By the end of this lesson you can

- List tracked state addresses and rename or relocate resources in state using terraform state mv
- Plan resource recreation using the -replace flag without modifying configuration files

## Where we are

Earlier lessons established that Terraform maintains a state file tracking deployed cloud infrastructure and maps configuration blocks to real resources. We also created root resources, such as an S3 bucket and compute modules with inputs and outputs, whose state Terraform manages during execution cycles.

## The idea

The `terraform state` command suite allows you to modify the Terraform state file without editing it directly ([source](https://developer.hashicorp.com/terraform/cli/commands/state)). The `terraform state list` command displays resource names and local identifiers tracked in the state file ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Read-only state subcommands like `list` do not create backup files ([source](https://developer.hashicorp.com/terraform/cli/commands/state)). Terraform state subcommands function with remote state in the same way they do with local state ([source](https://developer.hashicorp.com/terraform/cli/commands/state)).

The `terraform state mv` command moves resources between state files or renames resources within state without altering the configuration file ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Resource names must be unique within an intended state file ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). The `-state-out` flag in `terraform state mv` specifies the target destination state file for the moved resource ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Every `terraform state` subcommand that modifies state writes a backup file, and this behavior cannot be disabled ([source](https://developer.hashicorp.com/terraform/cli/commands/state)). Automatic backups generated during state modifications cannot be turned off ([source](https://developer.hashicorp.com/terraform/cli/commands/state)). In Terraform versions prior to 1.7, the `terraform state rm` command was used to remove resources from state ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

The `-replace` flag can be supplied to `terraform plan` and `terraform apply` to recreate specified resources without altering the configuration ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). The `terraform taint` command is deprecated in favor of the `-replace` flag for plan and apply operations ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). The `terraform refresh` command updates the state file to match changes made to physical resources outside of the Terraform workflow ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Terraform automatically executes a state refresh during plan, apply, and destroy operations by default ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

## Worked example

Consider refactoring an infrastructure component where a resource was initially declared as `resource "aws_instance" "web"`.

First, inspect the active state inventory by running `terraform state list`. The output confirms the resource address `aws_instance.web` is recorded.

Next, update your configuration in `main.tf` to rename the block from `resource "aws_instance" "web"` to `resource "aws_instance" "server"`. If you immediately execute `terraform plan`, Terraform detects `aws_instance.web` as missing and `aws_instance.server` as new, scheduling a destructive replacement.

To align state with the configuration without recreating the physical server, run:
`terraform state mv aws_instance.web aws_instance.server`
Terraform updates the state address, creates an automatic backup file of the state, and leaves the configuration file untouched. When you re-run `terraform plan`, Terraform reports no changes required.

Finally, if the running instance encounters an issue and requires recreation without changing any HCL files, you plan its replacement directly via the CLI:
`terraform plan -replace="aws_instance.server"`
Terraform displays an execution plan that will destroy and re-create `aws_instance.server` during the next apply.

## Your turn

You are refactoring the root configuration to prepare for moving state bindings. The S3 bucket previously labeled `data` has been renamed to `storage` in `main.tf`. Complete the `aws_s3_bucket.storage` resource block by restoring its `bucket` attribute to `"my-learning-bucket-2024"` so it matches the existing resource.

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
