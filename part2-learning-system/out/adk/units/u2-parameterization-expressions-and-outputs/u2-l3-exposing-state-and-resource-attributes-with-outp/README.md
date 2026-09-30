# Exposing State and Resource Attributes with Output Values

*Parameterization, Expressions, and Outputs*

## By the end of this lesson you can

- Declare root module outputs to display resource attributes and structured expressions on the command line
- Configure sensitive and ephemeral attributes on outputs to protect confidential infrastructure values

## Where we are

Earlier lessons established how to provision AWS networking and compute resources such as VPCs, subnets, and EC2 instances. You also learned how to use input variables and expressions like lookup and merge to dynamically configure infrastructure.

## The idea

Root module outputs display their values in the CLI output ([source](https://developer.hashicorp.com/terraform/language/values/outputs)). Terraform displays root module outputs on the command line interface after applying a configuration ([source](https://developer.hashicorp.com/terraform/language/values/outputs)). Other Terraform configurations can access root module outputs across state sharing using the terraform_remote_state data source ([source](https://developer.hashicorp.com/terraform/language/values/outputs)).

Output blocks can be used by child modules to expose resource attributes to parent modules ([source](https://developer.hashicorp.com/terraform/language/values/outputs)). Parent modules access child module outputs using the syntax module.<CHILD_MODULE_NAME>.<OUTPUT_NAME> ([source](https://developer.hashicorp.com/terraform/language/values/outputs)). The value argument of an output block accepts any valid expression ([source](https://developer.hashicorp.com/terraform/language/values/outputs)).

Setting the sensitive argument to true on an output prevents Terraform from showing its value in CLI output ([source](https://developer.hashicorp.com/terraform/language/values/outputs)). Terraform saves the values of sensitive outputs inside the state file ([source](https://developer.hashicorp.com/terraform/language/values/outputs)). Running the terraform output command with -json or -raw prints sensitive output values in plain text ([source](https://developer.hashicorp.com/terraform/language/values/outputs)). Marking an output with the ephemeral argument excludes the value from state and plan files ([source](https://developer.hashicorp.com/terraform/language/values/outputs)).

## Worked example

### Step 1: Define basic and structured outputs

Suppose we have an EC2 instance `aws_instance.web` and an S3 bucket `aws_s3_bucket.data`. We want to print the bucket ARN and instance ID upon completion:

```hcl
output "bucket_arn" {
  description = "ARN of the storage bucket"
  value       = aws_s3_bucket.data.arn
}

output "server_details" {
  description = "Key attributes for the compute server"
  value = {
    id        = aws_instance.web.id
    public_ip = aws_instance.web.public_ip
  }
}
```

The `value` argument accepts any valid expression, such as direct attribute references or inline maps.

### Step 2: Handle sensitive data

When exporting credentials or API tokens, add `sensitive = true`:

```hcl
output "admin_token" {
  description = "Bootstrap token for the application"
  value       = "token-secret-xyz"
  sensitive   = true
}
```

### Step 3: Observe output behavior

When running `terraform apply`, Terraform prints non-sensitive values directly to the CLI while redacting sensitive ones:

```text
Apply complete! Resources: 2 added, 0 changed, 0 destroyed.

Outputs:

admin_token = (sensitive value)
bucket_arn = "arn:aws:s3:::my-learning-bucket-2024"
server_details = {
  "id" = "i-0abcd1234ef567890"
  "public_ip" = "54.210.10.20"
}
```

Because Terraform saves sensitive outputs inside the state file, you can retrieve the plaintext value when needed in automation scripts by running:

```shell
terraform output -raw admin_token
```

## Your turn

Create `outputs.tf` to expose key infrastructure attributes and a sensitive secret:
1. `vpc_id`: Export the VPC ID from `aws_vpc.main.id`.
2. `public_subnet_ids`: Export a list containing the public subnet ID using splat syntax (`aws_subnet.public[*].id`).
3. `db_token`: Export the static credential string `"supersecret-token-123"` and configure `sensitive = true` so Terraform masks it in terminal output.

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
