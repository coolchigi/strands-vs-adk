# Remote state: risks, backends, and locking

*CLI Workflow and State*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the exercise has no .tftest.hcl checks

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Explain why storing state locally in version control is risky for teams and describe the recommended remote-backend alternative with locking

## Where we are

Earlier lessons established that Terraform records every resource it manages in a state file (`terraform.tfstate`). Previous exercises stored that file locally on disk, which is fine for solo work but breaks down the moment a second person is involved.

## The idea

## Why local state breaks in a team

With a local state file, every team member must ensure they have the latest state data before running Terraform, and must ensure no one else runs Terraform at the same time ([source](https://developer.hashicorp.com/terraform/language/state/remote)). This is impossible to guarantee with a file on someone's laptop or committed to a git repository — two engineers can run `terraform apply` simultaneously and corrupt each other's state ([source](https://developer.hashicorp.com/terraform/cli/commands/state)).

Committing `terraform.tfstate` to version control makes the problem worse, not better. Many Terraform resources store secret values — passwords, access keys, database credentials — in plaintext inside the state file ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-sensitive-data-secrets-manager-terraform/terraform-state-file.html)). Pushing that file to a public repository exposes those secrets to anyone who can read the repo ([source](https://developer.hashicorp.com/terraform/tutorials/modules/module-create)). Beyond confidentiality, failure to secure remote state can also lead to loss of state data, inability to manage infrastructure, and inadvertent resource deletion ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html)).

## The recommended solution: remote state with locking

With remote state, Terraform writes the state data to a remote data store that can be shared among all team members ([source](https://developer.hashicorp.com/terraform/language/state/remote)). The recommended alternative to keeping the file locally is to store it remotely — on a system designed for concurrent access ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html)). Remote state is implemented by configuring a backend (or HCP Terraform) in the configuration's root module ([source](https://developer.hashicorp.com/terraform/language/state/remote)). Terraform supports Amazon S3, Azure Blob Storage, Google Cloud Storage, HCP Terraform, HashiCorp Consul, and more ([source](https://developer.hashicorp.com/terraform/language/state/remote)).

Storing state remotely also removes it from disk entirely: when using a non-local backend, Terraform does not persist state to disk, which is a significant security benefit for sensitive values ([source](https://developer.hashicorp.com/terraform/language/state/backends)). For further protection, the state bucket should be encrypted with Amazon S3 server-side encryption (SSE) ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html)) and access should be restricted with bucket policies ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-sensitive-data-secrets-manager-terraform/terraform-state-file.html)).

## State locking

A remote backend that supports locking prevents two or more users from running Terraform simultaneously and ensures each run starts with the most recently updated state ([source](https://developer.hashicorp.com/terraform/language/state/purpose)). Not all backends support locking — the documentation for each backend states whether it does ([source](https://developer.hashicorp.com/terraform/language/state/backends)). Amazon S3 can lock Terraform state to help prevent corruption ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-sensitive-data-secrets-manager-terraform/terraform-state-file.html)). The standard pattern pairs an S3 bucket (state storage) with a DynamoDB table (lock tracking): Terraform writes a lock record to DynamoDB before it starts and removes it when it finishes, so a concurrent run fails fast instead of corrupting state ([source](https://developer.hashicorp.com/terraform/language/state/remote)).

Collaboration workflows should be structured in HCP Terraform or a CI/CD pipeline to limit who can access or modify state directly ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html)).

## Worked example

### Goal

Add a remote S3 backend to a root module, pairing it with a DynamoDB table for locking.

### Step 1 — Identify what the backend block needs

An S3 backend requires at minimum:
- `bucket` — the S3 bucket that holds the state file
- `key` — the path inside the bucket for this workspace's state
- `region` — the AWS region of the bucket
- `dynamodb_table` — the DynamoDB table used for locking
- `encrypt = true` — enables S3 server-side encryption at rest

### Step 2 — Write the `terraform` block

The `backend` block lives inside the `terraform {}` block in `terraform.tf`:

```hcl
terraform {
  required_version = ">= 1.1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  backend "s3" {
    bucket         = "my-company-tf-state"   # must already exist
    key            = "myproject/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "my-company-tf-locks"   # must already exist
    encrypt        = true
  }
}
```

### Step 3 — Understand what each piece does

| Argument | Purpose |
|---|---|
| `bucket` | Where Terraform reads and writes the state file ([source](https://developer.hashicorp.com/terraform/language/state/remote)) |
| `key` | Unique path so multiple workspaces can share one bucket without colliding |
| `region` | AWS region for both the bucket and the lock table |
| `dynamodb_table` | Table Terraform uses for distributed locking ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-sensitive-data-secrets-manager-terraform/terraform-state-file.html)) — prevents concurrent runs ([source](https://developer.hashicorp.com/terraform/language/state/purpose)) |
| `encrypt = true` | Enables SSE on the state object ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html)) |

### Step 4 — Migrate local state

After adding the block, run `terraform init`. Terraform detects the new backend and offers to copy the existing local state to the remote bucket. Accept, then delete the local `terraform.tfstate` so it can no longer be accidentally committed.

### Result

From this point on, every `terraform apply` (by any team member) will:
1. Attempt to acquire a lock in DynamoDB — failing immediately if another run holds it ([source](https://developer.hashicorp.com/terraform/language/state/purpose)).
2. Fetch the latest state from S3.
3. Write the updated state back to S3 and release the lock.
4. Never write state to local disk ([source](https://developer.hashicorp.com/terraform/language/state/backends)).

## Your turn

Add a remote S3 backend block to `terraform.tf` with DynamoDB locking.

Specifically:
1. Inside the `terraform {}` block, add a `backend "s3"` block with these exact values:
   - `bucket` = `"my-company-tf-state"`
   - `key` = `"myproject/dev/terraform.tfstate"`
   - `region` = `"us-east-1"`
   - `dynamodb_table` = `"my-company-tf-locks"`
   - `encrypt` = `true`
2. Keep all existing `required_version` and `required_providers` settings unchanged.

Run the checks with `terraform test` from the exercise folder (you do not need `terraform init` or a live AWS account — the checks use mock providers).

Nothing can check this exercise automatically, so you're the judge. When you're happy with it, `learn check` marks it done and `learn solution` shows the answer.

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
