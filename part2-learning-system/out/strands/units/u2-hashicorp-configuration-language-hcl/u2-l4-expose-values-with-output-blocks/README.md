# Expose values with output blocks

*HashiCorp Configuration Language (HCL)*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - The check for app_secret uses `nonsensitive(output.app_secret) == "s3cr3t-token-abc123"`, which passes whether or not `sensitive = true` is present. A learner who omits `sensitive = true` still passes the check, because `nonsensitive()` on an already-non-sensitive value is valid HCL and returns the...

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Write output blocks that expose the S3 bucket id and EC2 instance id, adding descriptions and marking a sensitive output appropriately
- Explain the four purposes of output values and where each applies (child module, CLI display, remote state, automation)

## Where we are

Earlier lessons introduced resources, variables, locals, and lifecycle rules. You now have a configuration that creates an S3 bucket and an EC2 instance, with variables declared in variables.tf and shared locals in locals.tf. This lesson adds outputs.tf to expose values from those resources.

## The idea

## What output values are for

Output values have four distinct purposes ([source](https://developer.hashicorp.com/terraform/language/values/outputs)):

1. **Child module → parent module.** When a resource lives inside a module, the only way to hand its attributes to the calling configuration is through an output block. ([source](https://developer.hashicorp.com/terraform/language/modules/configuration))
2. **CLI display.** Terraform displays root module output values in the terminal after `terraform apply` completes. ([source](https://developer.hashicorp.com/terraform/language/values/outputs))
3. **Remote state sharing.** A separate Terraform configuration can read root module outputs from state with the `terraform_remote_state` data source. ([source](https://developer.hashicorp.com/terraform/language/values/outputs))
4. **Automation integration.** An external tool such as a CI/CD pipeline can read output values from `terraform output` after an apply. ([source](https://developer.hashicorp.com/terraform/language/values/outputs))

## Writing an output block

Every output block needs a `value` argument. ([source](https://developer.hashicorp.com/terraform/language/values/outputs)) Adding a `description` is conventional so that readers of the configuration — teammates or your future self — understand what the value represents. ([source](https://developer.hashicorp.com/terraform/language/values/outputs)) A basic output block looks like this:

```hcl
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app.id
}
```

By convention, output definitions live in a file called `outputs.tf`. ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create))

## Marking an output sensitive

Some values — passwords, tokens, connection strings — should not appear in plain terminal output. Setting `sensitive = true` in the output block prevents Terraform from displaying the value in CLI output, showing a redacted message instead. ([source](https://developer.hashicorp.com/terraform/language/values/outputs)) If the value you are exporting already comes from a sensitive resource attribute, Terraform will actually *require* you to mark the output sensitive. ([source](https://developer.hashicorp.com/terraform/language/expressions/references))

Marking an output sensitive does **not** hide it from state. Terraform still stores the value in state, and `terraform output -json` or `terraform output -raw` will print it in plain text. ([source](https://developer.hashicorp.com/terraform/language/values/outputs))

```hcl
output "db_password" {
  description = "Database password (sensitive)"
  value       = aws_db_instance.main.password
  sensitive   = true
}
```

## Worked example

## Worked example: exposing a bucket name and a simulated secret

Suppose a configuration creates an S3 bucket and needs to expose its id, plus a simulated API token.

**Step 1 — identify the resource addresses.**  
The bucket is `aws_s3_bucket.assets`, so its id attribute is `aws_s3_bucket.assets.id`.  
The simulated secret is a plain string local, `local.fake_token`, just to demonstrate sensitivity.

**Step 2 — write the plain output.**  
The value is a direct attribute reference. A description documents intent for readers of the code.

```hcl
output "bucket_id" {
  description = "Name (id) of the S3 assets bucket"
  value       = aws_s3_bucket.assets.id
}
```

**Step 3 — write the sensitive output.**  
`sensitive = true` prevents the value from appearing in `terraform apply` terminal output. ([source](https://developer.hashicorp.com/terraform/language/values/outputs))

```hcl
output "api_token" {
  description = "Simulated API token (redacted in CLI)"
  value       = local.fake_token
  sensitive   = true
}
```

**Step 4 — apply and observe.**  
After `terraform apply`, the terminal shows something like:

```
Outputs:

api_token = <sensitive>
bucket_id = "my-learn-assets-2024"
```

The sensitive value is redacted. To retrieve it explicitly:

```bash
terraform output -raw api_token
# prints the plain value
```

`-raw` bypasses the redaction and prints the bare string. ([source](https://developer.hashicorp.com/terraform/tutorials/aws/aws-asg))

**Why two separate outputs?**  
The bucket id is safe to display everywhere; no special treatment is needed. The token is a secret; marking it sensitive means it will never accidentally appear in CI logs or shared terminal sessions. ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html))

## Your turn

Create outputs.tf in the same directory as main.tf. Define three outputs:
1. `bucket_id` — the S3 bucket's id, with a description.
2. `instance_id` — the EC2 instance's id, with a description.
3. `app_secret` — a simulated secret value (use the string literal `"s3cr3t-token-abc123"`), with a description, marked `sensitive = true`.

Then run `terraform apply` against LocalStack and confirm that `app_secret` is shown as `<sensitive>` in the terminal. Finally run `terraform output -raw app_secret` to confirm the plain value is still retrievable.

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
