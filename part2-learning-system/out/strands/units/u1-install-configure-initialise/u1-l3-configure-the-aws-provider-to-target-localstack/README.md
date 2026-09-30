# Configure the AWS provider to target LocalStack

*Install, Configure & Initialise*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the checks don't test the gap at provider.tf line 2: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.
> - the checks don't test the gap at provider.tf line 7: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.
> - the checks don't test the gap at provider.tf line 10: with just that left as the starter has it, the checks still pass. Test it, or fill it in for the learner.

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Write an AWS provider block that uses mock credentials, sets skip flags, and points service endpoints at LocalStack so no real AWS API calls are made
- Explain the purpose of each LocalStack-specific provider argument (skip_credentials_validation, skip_metadata_api_check, endpoints block)

## Where we are

Earlier lessons established that `terraform.tf` declares provider requirements with `required_providers`, pinning the AWS provider to `~> 6.0`. A separate provider block — placed in its own file — is where you supply runtime configuration such as credentials, region, and endpoints. Terraform merges all `.tf` files in the working directory automatically.

## The idea

## Provider blocks vs. required_providers

`required_providers` declares *which* provider to download and what version to accept. A `provider` block is where you configure *how* that provider connects to the API — authentication, region, and any overrides ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)). The two are separate: you need both, but they live in different places. Convention is to keep the provider block in its own `provider.tf` file ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)).

## What LocalStack needs

LocalStack emulates AWS services locally, and the AWS Terraform provider can target it through custom service endpoints ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)). Because LocalStack does not validate real AWS credentials, you supply mock values — `access_key = "test"` and `secret_key = "test"` — along with any valid region string ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)).

## Skip flags

Setting `skip_credentials_validation = true` tells the provider not to call the real AWS STS API to verify your credentials are genuine. Setting `skip_metadata_api_check = true` tells it not to query the EC2 instance metadata endpoint for credentials ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)). Both checks would fail or hang when the target is LocalStack rather than real AWS, so disabling them keeps `terraform init` and `terraform apply` fast and clean.

## The endpoints block

By default every AWS provider call goes to the real `amazonaws.com` URLs. The `endpoints` block overrides this on a per-service basis, pointing each service at a LocalStack URL instead ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)). Most services share `http://localhost:4566` ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)), but S3 uses the `s3.localhost.localstack.cloud:4566` hostname to support virtual-hosted-style bucket addressing ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)). Many services — EC2, IAM, Lambda, DynamoDB, and more — can each be listed individually in the same block ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)).

## A complete minimal configuration

Putting it together, a provider block ready for LocalStack looks like this :

```hcl
provider "aws" {
  access_key = "test"
  secret_key = "test"
  region     = "us-east-1"

  skip_credentials_validation = true
  skip_metadata_api_check     = true

  endpoints {
    s3  = "http://s3.localhost.localstack.cloud:4566"
    ec2 = "http://localhost:4566"
  }
}
```

No real AWS credentials are ever placed in the file ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)).

## Worked example

### Goal

Add a `provider.tf` file that configures the AWS provider for LocalStack, then verify it is syntactically correct with `terraform validate`.

---

**Step 1 — Create `provider.tf`**

Create a new file called `provider.tf` in your working directory. The provider's local name must be `aws` to match the `required_providers` entry ([source](https://developer.hashicorp.com/terraform/language/providers/requirements)).

```hcl
provider "aws" {
```

**Step 2 — Add mock credentials and region**

LocalStack accepts any non-empty strings for credentials ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)). Using `"test"` for both makes it obvious they are placeholders, not secrets.

```hcl
  access_key = "test"
  secret_key = "test"
  region     = "us-east-1"
```

**Step 3 — Disable the skip flags**

Without `skip_credentials_validation`, the provider would call real AWS STS to verify these credentials — and fail. Without `skip_metadata_api_check`, it tries the EC2 metadata endpoint — which also doesn't exist locally ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)).

```hcl
  skip_credentials_validation = true
  skip_metadata_api_check     = true
```

**Step 4 — Add the endpoints block**

S3 gets the virtual-hosted hostname; EC2 uses the plain localhost address ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)) ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)).

```hcl
  endpoints {
    s3  = "http://s3.localhost.localstack.cloud:4566"
    ec2 = "http://localhost:4566"
  }
}
```

**Step 5 — Run `terraform validate`**

```
$ terraform validate
Success! The configuration is valid.
```

`terraform validate` checks HCL syntax and provider schema without contacting any API, so it works even without LocalStack running ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)). If it reports errors, check for missing `=` signs, unclosed braces, or a typo in the provider name.

## Your turn

Create a `provider.tf` file in the same folder as your existing `main.tf` and `terraform.tf`. It must contain an `aws` provider block with: `access_key = "test"`, `secret_key = "test"`, `region = "us-east-1"`, `skip_credentials_validation = true`, `skip_metadata_api_check = true`, and an `endpoints` block that points `s3` to `http://s3.localhost.localstack.cloud:4566` and `ec2` to `http://localhost:4566`. Run `terraform init` then the tests with `terraform test`.

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
