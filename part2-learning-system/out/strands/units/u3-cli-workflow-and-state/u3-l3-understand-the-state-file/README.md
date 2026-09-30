# Understand the state file

*CLI Workflow and State*

> **Known problems.** This lesson didn't pass all of our own checks. If something below doesn't work, it may be this:
>
> - the untouched starter already passes the checks, so there is nothing to do

Found something else? `learn report "what's wrong"`

## By the end of this lesson you can

- Explain what terraform.tfstate contains (resource map, dependencies, provider pointer, cached attributes) and why Terraform cannot plan without it
- Identify the risk of editing the state file directly and state the correct alternative

## Where we are

Earlier lessons introduced Terraform configuration files and showed how `terraform apply` provisions real infrastructure. You also saw that provider and variable files drive what Terraform creates. This lesson looks at what Terraform writes *after* an apply: the state file that lets it manage infrastructure across runs.

## The idea

## What Is the State File?

Terraform stores state locally in a file named `terraform.tfstate` in the working directory where you run Terraform commands ([source](https://developer.hashicorp.com/terraform/language/state/remote)). It is a JSON-encoded file that Terraform writes and reads at each operation ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). The file is plain text and includes both sensitive and non-sensitive data about deployed infrastructure ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/secure-sensitive-data-secrets-manager-terraform/terraform-state-file.html)).

## What the State File Contains

The state file records four closely related things:

**1. Resource map.** Terraform maps each configuration resource block to a real-world object. For example, `resource "aws_instance" "app"` in your configuration is recorded alongside the actual instance ID that was assigned when the resource was created ([source](https://developer.hashicorp.com/terraform/language/state/purpose)). This lets Terraform look at your configuration and know exactly which remote object to update or destroy.

**2. Dependencies.** Terraform stores metadata about inter-resource dependencies under a `dependencies` key in each resource's entry ([source](https://developer.hashicorp.com/terraform/language/state/purpose)). This is how Terraform knows the correct order to destroy resources even if you later remove them from the configuration — the dependency record is already in state ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

**3. Provider pointer.** Each resource entry carries a pointer to the provider configuration that was most recently used with it. This matters when multiple aliased providers exist and Terraform needs to know which one to call ([source](https://developer.hashicorp.com/terraform/language/state/purpose)).

**4. Cached attributes.** Terraform caches every attribute value for every resource in state as a performance optimisation, so it does not have to query every provider API on every plan or apply ([source](https://developer.hashicorp.com/terraform/language/state/purpose)). Attribute values are stored as resolved plain text, not as the variable-interpolated expressions that appear in your `.tf` files ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

The `mode` key on each resource entry tells you whether it is a managed resource (`managed`) or a data source (`data`) ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

## Why Terraform Cannot Plan Without State

Terraform compares your configuration with the state file and your existing infrastructure to create plans and make changes ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Without a matching state file it cannot determine what infrastructure it already manages, so it has no baseline to diff against — it would treat everything as new ([source](https://docs.aws.amazon.com/prescriptive-guidance/latest/terraform-aws-provider-best-practices/security.html)).

## Never Edit State Directly

You should never manually edit the state file ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Any manual change risks creating drift between your configuration, your state, and the real infrastructure, and that drift can cause Terraform to destroy and recreate resources on the next apply ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). The correct alternative is the `terraform state` sub-commands (such as `terraform state mv` or `terraform state rm`), which manipulate state safely with proper locking and validation.

## Worked example

## Reading a Real State File

After running `terraform apply` against the configuration from the previous lesson, Terraform writes `terraform.tfstate`. Below is an **abbreviated** extract showing the `aws_subnet.public[0]` resource entry — chosen because it depends on `aws_vpc.main` via its `vpc_id` argument, so it demonstrates all four state concepts at once.

```json
{
  "version": 4,
  "terraform_version": "1.16.4",
  "serial": 3,
  "lineage": "a1b2c3d4-...",
  "resources": [
    {
      "mode": "managed",
      "type": "aws_subnet",
      "name": "public",
      "provider": "provider[\"registry.terraform.io/hashicorp/aws\"]",
      "instances": [
        {
          "index_key": 0,
          "schema_version": 1,
          "attributes": {
            "id": "subnet-0abc1234",
            "cidr_block": "10.0.0.0/24",
            "availability_zone": "us-east-1a",
            "vpc_id": "vpc-0def5678",
            "tags": {
              "Name": "public-0",
              "Project": "myproject-dev"
            }
          },
          "dependencies": [
            "aws_vpc.main"
          ]
        }
      ]
    }
  ]
}
```

Let's walk through each concept:

**Resource map** — The three fields `"type": "aws_subnet"`, `"name": "public"`, and `"provider": "provider[\"registry.terraform.io/hashicorp/aws\"]"` together form the mapping. Terraform knows that the Terraform resource called `aws_subnet.public[0]` corresponds to the real AWS subnet with ID `subnet-0abc1234` ([source](https://developer.hashicorp.com/terraform/language/state/purpose)).

**Dependencies** — The `"dependencies": ["aws_vpc.main"]` array tells Terraform that this subnet depends on the VPC ([source](https://developer.hashicorp.com/terraform/language/state/purpose)). Notice the direction: `aws_subnet.public` lists `aws_vpc.main` as a dependency because the subnet's `vpc_id` argument references `aws_vpc.main.id`. The VPC entry itself has an empty dependencies array, because nothing it needs already exists. If you removed `aws_vpc.main` from your configuration, Terraform would still know to destroy the subnet before the VPC ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)).

**Provider pointer** — The `"provider"` field at the resource level (not inside `instances`) records which provider configuration last managed this resource. With a single provider this is straightforward; with multiple aliased `aws` providers it disambiguates which region or account owns the resource ([source](https://developer.hashicorp.com/terraform/language/state/purpose)).

**Cached attributes** — Everything inside `"attributes"` is cached: `cidr_block`, `availability_zone`, `vpc_id`, `tags`, and so on. These are the resolved, plain-text values — `"10.0.0.0/24"` rather than `cidrsubnet(var.vpc_cidr, 8, count.index)` ([source](https://developer.hashicorp.com/terraform/language/state/purpose)) ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). Terraform uses this cache so it can compute a diff on the next plan without calling AWS for every resource ([source](https://developer.hashicorp.com/terraform/language/state/purpose)).

**What would happen if you deleted the file?** Terraform would have no record of the subnet, the VPC, the EC2 instance, or the S3 buckets. On the next `terraform plan` it would conclude that all of those resources need to be *created*, producing a plan full of `+` additions — even though the real infrastructure is sitting there unchanged ([source](https://developer.hashicorp.com/terraform/tutorials/state/state-cli)). It would not destroy what already exists, but it would try to create duplicates, which would either fail (for resources with unique names) or create unwanted extras.

## Your turn

Run `terraform apply -auto-approve` against the LocalStack configuration to produce a populated `terraform.tfstate` file. Then open the file in a text editor and complete the three inspection tasks written as TODO comments in `inspect_state.md`. Finally, confirm your understanding by answering the deletion scenario at the bottom of that file.

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
