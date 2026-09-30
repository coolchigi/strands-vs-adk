# Inspecting State and Output Extraction

*State Inspection, Management, and Refactoring*

## By the end of this lesson you can

- Inspect current state snapshots and plan files in human-readable and JSON formats using terraform show
- Extract specific root module output values in plain text and JSON formats using terraform output

## Where we are

In earlier lessons, we decomposed infrastructure into reusable child modules for VPC and compute resources and passed data between them using module inputs and outputs. We also declared root outputs to expose key identifiers such as VPC IDs and instance IDs for consumption.

## The idea

The `terraform show` command provides human-readable output from a state file or a plan file ([source](https://developer.hashicorp.com/terraform/cli/commands/show)). If you do not specify a file path, Terraform defaults to displaying the latest state snapshot ([source](https://developer.hashicorp.com/terraform/cli/commands/show)). Running `terraform show` displays all the resources currently tracked in Terraform state ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). You can also pass the `-no-color` flag to disable color formatting in the output ([source](https://developer.hashicorp.com/terraform/cli/commands/show)).

The `-json` option causes `terraform show` to output machine-readable JSON representing a state or plan file ([source](https://developer.hashicorp.com/terraform/cli/commands/show)). For state files, including when no path is provided, `terraform show -json` produces a JSON representation of the state ([source](https://developer.hashicorp.com/terraform/cli/commands/show)). When using the `-json` command-line flag, any sensitive values stored in Terraform state will be displayed in plain text ([source](https://developer.hashicorp.com/terraform/cli/commands/show)).

The `terraform output` command extracts output variable values directly from the state file ([source](https://developer.hashicorp.com/terraform/cli/commands/output)). The `terraform output` command only displays outputs defined in the root module ([source](https://developer.hashicorp.com/terraform/cli/commands/output)). To view outputs from child modules via `terraform output`, you must expose them through an output block defined in your root module ([source](https://developer.hashicorp.com/terraform/cli/commands/output)). With no additional arguments, `terraform output` displays every output defined in the root module ([source](https://developer.hashicorp.com/terraform/cli/commands/output)). If an output name is specified, only the value of that specific output is printed ([source](https://developer.hashicorp.com/terraform/cli/commands/output)).

The `-json` flag formats output values as a JSON object with a key per output, or returns only the specified output if an output name is provided ([source](https://developer.hashicorp.com/terraform/cli/commands/output)). The `-raw` flag converts a specified output value to a string and prints it directly without special formatting, but it only supports string, number, and boolean types ([source](https://developer.hashicorp.com/terraform/cli/commands/output)). The `-no-color` flag disables color in the output ([source](https://developer.hashicorp.com/terraform/cli/commands/output)). Additionally, the legacy `-state=path` option specifies the path to a state file for the local backend, defaulting to `terraform.tfstate` ([source](https://developer.hashicorp.com/terraform/cli/commands/output)).

Terraform displays `<sensitive>` when listing all outputs, but does not redact sensitive values when an output is queried specifically by name ([source](https://developer.hashicorp.com/terraform/cli/commands/output)). When using either the `-json` or `-raw` flags, Terraform displays sensitive values in plain text rather than masking them ([source](https://developer.hashicorp.com/terraform/cli/commands/output)). However, Terraform completely omits ephemeral values from `terraform output` entirely, even when queried by name, because ephemeral values are never stored in state ([source](https://developer.hashicorp.com/terraform/cli/commands/output)).

## Worked example

Consider a configuration where a root module calls a database module and defines outputs:

```hcl
# outputs.tf
output "db_host" {
  description = "Database endpoint"
  value       = module.database.endpoint
}

output "db_password" {
  description = "Admin password"
  value       = var.admin_password
  sensitive   = true
}
```

1. **Inspecting current state**:
   Running `terraform show` prints every resource tracked in the state file in a human-readable format resembling HCL blocks. Running `terraform show -json` emits the entire state snapshot as machine-readable JSON, exposing resource attributes and sensitive state values in plain text.

2. **Inspecting all root outputs**:
   Running `terraform output` lists every root module output:
   ```text
   db_host = "mydb.cluster.internal"
   db_password = <sensitive>
   ```
   Notice that `db_password` is masked as `<sensitive>` when listing all outputs.

3. **Querying a specific output by name**:
   Running `terraform output db_password` prints the plaintext password directly: Terraform does not redact sensitive values when queried by name.

4. **Extracting values for shell pipelines**:
   Running `terraform output -raw db_host` outputs `mydb.cluster.internal` without quotes or newline decoration, making it suitable for direct assignment into shell variables: `export DB_HOST=$(terraform output -raw db_host)`. Running `terraform output -json` outputs a JSON structure containing both outputs, rendering `db_password` in plain text.

## Your turn

Configure root module outputs so that state inspection and output extraction commands can query the VPC CIDR from the child module and extract an application API token.

1. In `outputs.tf`, expose the VPC CIDR block from the child module `module.vpc.vpc_cidr` as a root output named `vpc_cidr`.
2. In `outputs.tf`, expose `var.api_token` as a root output named `api_token` and mark it with `sensitive = true`.

Once declared, running `terraform show` and `terraform show -json` will include these attributes in state, while `terraform output` will allow querying them with `-raw` and `-json`.

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
