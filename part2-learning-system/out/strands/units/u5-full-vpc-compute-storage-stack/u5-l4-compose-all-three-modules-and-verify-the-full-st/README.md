# Compose all three modules and verify the full stack

*Full VPC, Compute & Storage Stack*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - Quiz Q1 option C (adding depends_on inside an output block) is not valid Terraform syntax. No learner who has worked through the lesson would hold this misconception, so it does not function as a plausible distractor. Replace it with a wrong answer a learner might genuinely reach for, such as...
> - Quiz Q2 says the teammate runs terraform output inside the modules/networking directory. That directory has no state file and no initialised working directory, so the command would error on a missing backend rather than silently show nothing. The stem conflates two different problems (no state vs....

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Wire all three modules in the root module, threading networking outputs into compute and storage inputs, and expose final outputs for subnet IDs and instance IPs in root outputs.tf
- Apply the full stack to LocalStack, verify each resource tier using AWS CLI commands, and destroy the stack cleanly, confirming an empty state file

## Where we are

Earlier lessons built three child modules — networking, compute, and storage — each with their own `variables.tf`, `main.tf`, and `outputs.tf`. The root `main.tf` already calls all three modules, including a `for_each` loop over the storage module that creates two instances addressed as `module.storage["my-project-assets"]` and `module.storage["my-project-logs"]`. Outputs inside a child module are only surfaced to the caller when the root `outputs.tf` explicitly re-exports them.

## The idea

## Module composition: threading outputs into inputs

Module composition is the flat style of passing outputs from one module as inputs to another, rather than embedding dependencies inside a module ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)). Cross-module dependencies are expressed by referencing one module's outputs directly in another module's input arguments using the `module.<name>.<output>` syntax ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)). For example, in a root module, outputs from a networking module such as `vpc_id` and `subnet_ids` are passed as input variables to dependent modules like a compute module ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)).

All arguments in a module block other than `source` and `version` are treated as input variables for that module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)). So writing `subnet_ids = module.networking.subnet_ids` inside the compute module block passes the networking module's `subnet_ids` output directly as the compute module's `subnet_ids` input variable ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)).

Terraform strongly recommends keeping the module tree flat with only one level of child modules, using expressions to describe relationships between modules ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)).

## Re-exporting outputs from the root module

Outputs are the only supported way for users to get information about resources configured inside a module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). Module outputs are referenced with the `module.MODULE_NAME.OUTPUT_NAME` convention, and must be explicitly re-exported in the root module's `outputs.tf` to be displayed ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)).

The root module's `outputs.tf` can reference child module outputs to expose them ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). For a module called with `for_each`, each instance is addressed by its key, so `module.storage["my-project-assets"].bucket_id` reaches the `bucket_id` output of that specific instance. The root `outputs.tf` exposes values such as the VPC's public subnet IDs and the EC2 instances' public IPs by referencing child module outputs ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)).

## Verifying the stack with the AWS CLI

After `terraform apply` completes, Terraform prints the declared root outputs directly in the terminal ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)). You can also verify resources directly:

- **VPC**: `aws ec2 describe-vpcs` lists all VPCs and returns attributes including `CidrBlock`, `VpcId`, and `State` ([source](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html)) ([source](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html)).
- **Instances**: `aws ec2 describe-instances` with `--instance-ids` retrieves details for specific instances ([source](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html)), including `SubnetId` and `VpcId` fields to confirm correct placement ([source](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html)).
- **S3**: `aws s3 ls` lists all buckets owned by the authenticated user ([source](https://docs.aws.amazon.com/cli/latest/reference/s3/ls.html)).

## Destroying the stack

Running `terraform destroy` removes all managed resources; it shows a plan of what will be destroyed and requires confirming with `yes` ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). After `terraform destroy` completes, the `terraform.tfstate` file still exists but contains an empty resources list, confirming all resources were removed ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). The empty state file has a `"resources"` key set to an empty array ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

## Worked example

# Worked example: wiring two modules and re-exporting their outputs

Suppose you have a `networking` module that exposes `vpc_id` and `subnet_ids`, and a `compute` module that accepts `subnet_ids`. Here is how to compose them and surface their outputs.

**Step 1 — Call both modules in `main.tf`, threading the output into the input**

```hcl
module "networking" {
  source = "./modules/networking"

  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
}

module "compute" {
  source = "./modules/compute"

  ami_id     = "ami-0c55b159cbfafe1f0"
  subnet_ids = module.networking.subnet_ids   # output → input
}
```

`subnet_ids = module.networking.subnet_ids` is a cross-module dependency expressed directly in the module block argument ([source](https://developer.hashicorp.com/terraform/language/modules/develop/composition)). All arguments other than `source` and `version` are treated as input variables for the module ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)), so this passes the networking module's list of subnet IDs straight into the compute module's `subnet_ids` variable.

**Step 2 — Add a `for_each` storage module**

```hcl
module "storage" {
  for_each = toset(["assets", "logs"])

  source      = "./modules/storage"
  bucket_name = each.key
}
```

Because `for_each` was used, Terraform creates two instances: `module.storage["assets"]` and `module.storage["logs"]`. Each instance is addressed by its map key.

**Step 3 — Re-export outputs in root `outputs.tf`**

Module outputs must be explicitly re-exported in the root module's `outputs.tf` to be displayed ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)):

```hcl
output "subnet_ids" {
  description = "Public subnet IDs."
  value       = module.networking.subnet_ids
}

output "instance_ids" {
  description = "EC2 instance IDs."
  value       = module.compute.instance_ids
}

output "assets_bucket_id" {
  description = "Assets bucket name."
  value       = module.storage["assets"].bucket_id
}

output "logs_bucket_id" {
  description = "Logs bucket name."
  value       = module.storage["logs"].bucket_id
}
```

`module.storage["assets"].bucket_id` addresses the `bucket_id` output of the `"assets"` instance of the `for_each` module. After `terraform apply`, Terraform prints these declared outputs directly in the terminal ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-use)).

**Step 4 — Verify with the AWS CLI**

```bash
# Check the VPC exists and note its CidrBlock and State
aws ec2 describe-vpcs

# Check instances and confirm SubnetId matches a networking output
aws ec2 describe-instances \
  --query 'Reservations[*].Instances[*].{ID:InstanceId,Subnet:SubnetId}' \
  --output json

# List all buckets to confirm both were created
aws s3 ls
```

The `describe-vpcs` response includes `CidrBlock`, `VpcId`, and `State` ([source](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-vpcs.html)). The `describe-instances` response includes `SubnetId` and `VpcId` confirming correct placement ([source](https://docs.aws.amazon.com/cli/latest/reference/ec2/describe-instances.html)). `aws s3 ls` lists all buckets owned by the authenticated user ([source](https://docs.aws.amazon.com/cli/latest/reference/s3/ls.html)).

**Step 5 — Destroy and confirm empty state**

```bash
terraform destroy   # type 'yes' at the prompt
cat terraform.tfstate
```

After destroy, the state file contains `"resources": []` — an empty array confirming all resources were removed ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

## Your turn

You are given all three child modules (networking, compute, storage) already complete, plus a root `terraform.tf` and `provider.tf`. Your tasks are:

1. In root `main.tf`: call `module.networking`, `module.compute` (passing `subnet_ids = module.networking.subnet_ids`), and `module.storage` with a `for_each` over `["my-project-assets", "my-project-logs"]` using `bucket_name = each.key`.
2. In root `outputs.tf`: re-export `module.networking.subnet_ids` as `networking_subnet_ids`, `module.compute.instance_ids` as `compute_instance_ids`, `module.storage["my-project-assets"].bucket_id` as `assets_bucket_id`, and `module.storage["my-project-logs"].bucket_id` as `logs_bucket_id`.
3. Run `terraform init`, then `terraform apply -auto-approve`.
4. Run `aws --endpoint-url=http://localhost:4566 ec2 describe-vpcs`, `aws --endpoint-url=http://localhost:4566 ec2 describe-instances`, and `aws --endpoint-url=http://localhost:4566 s3 ls` to verify each tier.
5. Run `terraform destroy -auto-approve` and inspect `terraform.tfstate` to confirm `"resources": []`.

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
