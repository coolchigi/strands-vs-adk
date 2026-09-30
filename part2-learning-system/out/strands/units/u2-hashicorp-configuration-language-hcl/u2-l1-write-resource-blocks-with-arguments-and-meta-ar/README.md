# Write resource blocks with arguments and meta-arguments

*HashiCorp Configuration Language (HCL)*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - u2-l1: 'Predict the effect of create_before_destroy and ignore_changes lifecycle arguments on a planned replacement' asks the learner to analyze, and a quiz can't show that. It needs an exercise.
> - The exercise task explicitly requires a lifecycle block with `create_before_destroy = true`, and the solution includes it, but none of the three checks assert anything about the lifecycle block. A learner can omit it entirely and still pass all checks. The check for the exercise's stated objective...
> - All three quiz questions target the single objective 'Predict the effect of create_before_destroy and ignore_changes lifecycle arguments on a planned replacement'. There is no quiz question covering the other practised skill — writing a resource block with the correct labels and required arguments...
> - The claim that `create_before_destroy = true` provisions the replacement before tearing down the original is cited as `c:5173ec833c69` in the explanation but as `c:95861c25bb7a` in the worked example (Step 3). These are different citation IDs for the same factual claim; one of them is unsupported...

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Write resource blocks for an S3 bucket and an EC2 instance, setting required arguments and at least one lifecycle meta-argument
- Predict the effect of create_before_destroy and ignore_changes lifecycle arguments on a planned replacement

## Where we are

Earlier lessons established the provider block, the `terraform {}` configuration block, and how Terraform initialises a working directory. This lesson uses those foundations to write the first real infrastructure resources.

## The idea

## Resource blocks

Every piece of infrastructure Terraform manages is declared as a **resource block**. The block has two labels — the resource type and a local name — followed by a body of arguments ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)). A minimal S3 bucket only needs the `bucket` argument ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)). An EC2 instance requires at minimum `ami` and `instance_type` ([source](https://developer.hashicorp.com/terraform/language/block/resource)).

```hcl
resource "aws_s3_bucket" "assets" {
  bucket = "my-assets-bucket"
}

resource "aws_instance" "app" {
  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"
}
```

## The lifecycle meta-argument

Every resource block accepts an optional `lifecycle` block that controls how Terraform creates, updates, and destroys that resource ([source](https://developer.hashicorp.com/terraform/language/block/resource)). Because Terraform processes the lifecycle block before evaluating other expressions, its values must be literals — no variables or references ([source](https://developer.hashicorp.com/terraform/language/block/resource)).

The three most commonly used directives are:

- **`create_before_destroy = true`** — Terraform provisions the replacement resource first, then tears down the original, so there is no gap in availability ([source](https://developer.hashicorp.com/terraform/language/block/resource)).
- **`ignore_changes = [attr, ...]`** — Terraform ignores the listed attributes when planning updates, so it will not try to revert changes made outside Terraform (for example, auto-scaling changing `desired_capacity`) ([source](https://developer.hashicorp.com/terraform/language/block/resource)) ([source](https://developer.hashicorp.com/terraform/tutorials/aws/aws-asg)).
- **`prevent_destroy = true`** — Terraform returns an error if a plan would destroy the resource; however, removing the resource block entirely still allows destruction ([source](https://developer.hashicorp.com/terraform/language/block/resource)).

```hcl
resource "aws_instance" "app" {
  ami           = "ami-a1b2c3d4"
  instance_type = "t2.micro"

  lifecycle {
    create_before_destroy = true
  }
}
```

## Worked example

### Goal
Declare an S3 bucket and an EC2 instance, and add a `lifecycle` block to the instance.

---

**Step 1 — S3 bucket resource**

The only required argument is `bucket` ([source](https://docs.localstack.cloud/aws/connecting/infrastructure-as-code/terraform/)):

```hcl
resource "aws_s3_bucket" "assets" {
  bucket = "my-project-assets"
}
```

Label one: `aws_s3_bucket` (the type Terraform will call the AWS API for).
Label two: `assets` (the local name used to reference this resource elsewhere).

---

**Step 2 — EC2 instance resource**

`ami` and `instance_type` are both required ([source](https://developer.hashicorp.com/terraform/language/block/resource)):

```hcl
resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"
}
```

---

**Step 3 — Add a lifecycle block**

We want zero downtime on replacement, so we use `create_before_destroy` ([source](https://developer.hashicorp.com/terraform/tutorials/aws/aws-asg)):

```hcl
resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  lifecycle {
    create_before_destroy = true
  }
}
```

Terraform processes `lifecycle` before evaluating expressions, so the value **must** be the literal `true`, not a variable ([source](https://developer.hashicorp.com/terraform/language/block/resource)).

---

**Step 4 — Read the plan**

Running `terraform plan` against a local endpoint produces output like:

```
Terraform will perform the following actions:

  # aws_s3_bucket.assets will be created
  + resource "aws_s3_bucket" "assets" {
      + bucket = "my-project-assets"
      ...
    }

  # aws_instance.app will be created
  + resource "aws_instance" "app" {
      + ami           = "ami-0c55b159cbfafe1f0"
      + instance_type = "t3.micro"
      ...
    }

Plan: 2 to add, 0 to change, 0 to destroy.
```

Both resources show `+ (create)`. The `create_before_destroy` directive does not change the first-time plan (nothing exists yet to replace), but it would change the order on a future replacement.

## Your turn

Starting from the previous lesson's files, replace `main.tf` with one that declares two resources:

1. An `aws_s3_bucket` named `assets` with `bucket = "tf-learn-assets-bucket"`.
2. An `aws_instance` named `app` with `ami = "ami-0c55b159cbfafe1f0"` and `instance_type = "t3.micro"`, plus a `lifecycle` block that sets `create_before_destroy = true`.

Keep `terraform.tf` and `provider.tf` exactly as they are. Run the checks with `terraform test` to verify.

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
