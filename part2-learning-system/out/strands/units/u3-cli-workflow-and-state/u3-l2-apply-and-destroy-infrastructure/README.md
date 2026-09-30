# Apply and destroy infrastructure

*CLI Workflow and State*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - In the worked example, citation c:27202231642d is used to support two distinct claims: (1) that outputs are displayed after apply, and (2) that sensitive outputs appear as `<sensitive>` in the terminal. In the explanation section, c:27202231642d is cited only for claim (1). If the source page...
> - The lesson title and all three objectives centre on `terraform apply` and `terraform destroy`, but the only hands-on work the learner actually authors in the exercise is declaring two output blocks in `outputs.tf`. Writing output declarations was the subject of the previous lesson; it is not...

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Apply the saved plan file to LocalStack, confirm the state file is updated, and verify outputs are printed
- Run terraform destroy, confirm the prompt, and verify the state file shows an empty resources list

## Where we are

The previous lesson covered `terraform plan`, which produces an execution plan describing what Terraform will create, change, or destroy — and how to save that plan to a file with `-out=tfplan`. We also declared outputs in `outputs.tf` and variables in `variables.tf`, and initialised the working directory with `terraform init`.

## The idea

## Applying a saved plan

`terraform apply` executes the operations proposed in a Terraform plan ([source](https://developer.hashicorp.com/terraform/cli/commands/apply)). When you pass a saved plan file to `terraform apply`, Terraform performs the operations in the saved plan without prompting you for confirmation ([source](https://developer.hashicorp.com/terraform/cli/commands/apply)). This is because Terraform interprets the act of passing the plan file as the approval ([source](https://developer.hashicorp.com/terraform/cli/commands/apply)).

When run **without** a saved plan file, `terraform apply` automatically creates a new execution plan, prompts you to approve it, and then performs the indicated operations ([source](https://developer.hashicorp.com/terraform/cli/commands/apply)). The confirmation prompt requires you to type `yes` before any changes are made ([source](https://developer.hashicorp.com/terraform/tutorials/configuration-language/for-each)).

Passing a saved plan file is useful for reliability: it allows you to apply an exact set of pre-approved changes, even if the configuration or the state of the real infrastructure has changed in the minutes since the original plan was created ([source](https://developer.hashicorp.com/terraform/cli/run)). When using a saved plan, you cannot specify any additional planning modes or options, because the plan file already contains the final decisions ([source](https://developer.hashicorp.com/terraform/cli/commands/apply)).

## What happens after apply

After a successful `terraform apply`, Terraform updates the state file with any changes to your resources ([source](https://developer.hashicorp.com/terraform/cli/commands/apply)). The apply output ends with a summary line such as `Apply complete! Resources: N added, 0 changed, 0 destroyed.` ([source](https://developer.hashicorp.com/terraform/tutorials/aws/aws-asg)). Terraform also displays root module output values in the CLI after you apply your configuration ([source](https://developer.hashicorp.com/terraform/language/values/outputs)).

## Destroying infrastructure

`terraform destroy` destroys all resources managed by the current working directory and workspace, using state data to identify which real-world objects correspond to managed resources ([source](https://developer.hashicorp.com/terraform/cli/run)). Like `terraform apply`, it asks for confirmation before proceeding ([source](https://developer.hashicorp.com/terraform/cli/run)). You must type `yes` at the prompt ([source](https://developer.hashicorp.com/terraform/tutorials/configuration-language/for-each)).

A destroy behaves exactly like deleting every resource from the configuration and then running an apply, except that it does not require editing the configuration ([source](https://developer.hashicorp.com/terraform/cli/run)). This is more convenient if you intend to provision similar resources at a later date ([source](https://developer.hashicorp.com/terraform/cli/run)).

After `terraform destroy` completes, the state file still exists but contains an empty `resources` list, confirming all resources were removed ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). The `resources` key is set to an empty array ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

## Worked example

## Worked example: apply a saved plan, then destroy

Suppose you ran `terraform plan -out=tfplan` in the previous lesson and now want to apply that plan against LocalStack.

### Step 1 — Apply the saved plan

```
terraform apply tfplan
```

Because you passed the saved plan file, Terraform skips the confirmation prompt and immediately begins creating resources ([source](https://developer.hashicorp.com/terraform/cli/commands/apply)). You see each resource being created as it streams output to the terminal.

```
aws_vpc.main: Creating...
aws_vpc.main: Creation complete after 0s [id=vpc-0abc1234]
aws_s3_bucket.env["logs"]: Creating...
...
Apply complete! Resources: 6 added, 0 changed, 0 destroyed.

Outputs:

bucket_ids     = ["backups", "logs"]
instance_id    = "i-0deadbeef00000001"
instance_ami   = "ami-0deadbeef00000000"
instance_type  = "t3.small"
subnet_ids     = ["subnet-0001", "subnet-0002", "subnet-0003"]
app_secret     = <sensitive>
```

Outputs are displayed at the end of the apply ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Sensitive outputs are shown as `<sensitive>` in the terminal ([source](https://developer.hashicorp.com/terraform/language/values/outputs)).

### Step 2 — Inspect the state file

Open `terraform.tfstate` in your editor and search for `aws_instance`. You will find a block similar to:

```json
{
  "type": "aws_instance",
  "name": "app",
  "instances": [
    {
      "attributes": {
        "id": "i-0deadbeef00000001",
        ...
      }
    }
  ]
}
```

After a successful apply Terraform has written every resource's real attributes into the state file ([source](https://developer.hashicorp.com/terraform/cli/commands/apply)).

### Step 3 — Destroy all resources

```
terraform destroy
```

Terraform shows a plan of everything it will destroy and then asks:

```
Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes
```

Type `yes` and press Enter ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). Terraform tears down every resource and prints:

```
Destroy complete! Resources: 6 destroyed.
```

### Step 4 — Verify the empty state

Open `terraform.tfstate` again. The file now contains `"resources": []`, confirming no managed resources remain ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)):

```json
{
  "version": 4,
  "terraform_version": "1.16.4",
  "serial": 12,
  "lineage": "...",
  "outputs": {},
  "resources": [],
  "check_results": null
}
```

The state file still exists; it just has nothing left to track ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

## Your turn

You have a plan file called `tfplan` already saved from the previous lesson (the starter includes a helper that writes it for you on `terraform init`). Do the following steps:

1. Run `terraform apply tfplan` to apply the saved plan against LocalStack. Observe that no confirmation prompt appears.
2. Open `terraform.tfstate` and find the `id` attribute of `aws_instance.app`.
3. Run `terraform output` to see the declared output values printed to the terminal.
4. Run `terraform destroy`, type `yes` at the prompt, then open `terraform.tfstate` and verify the `resources` array is empty.

The checks verify the final state of your Terraform configuration — make sure all files match what is expected before running them.

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
