# State File Inspection

After running `terraform apply -auto-approve`, open `terraform.tfstate` in a text editor
and answer each question by filling in the blanks below.

## Part A – Resource identity

Find the entry for `aws_subnet.public[0]` in the state file.

- type:     aws_subnet
- name:     public
- provider: provider["registry.terraform.io/hashicorp/aws"]

## Part B – Dependencies

Still on `aws_subnet.public[0]`, find the `dependencies` array inside its instance entry.

- dependencies: aws_vpc.main

Now find the entry for `aws_vpc.main`.

- dependencies: empty

## Part C – Cached attribute

Still on `aws_subnet.public[0]`, look inside the `attributes` object.

- cidr_block value in state: 10.0.0.0/24
- What expression produced it in main.tf? cidrsubnet(var.vpc_cidr, 8, count.index)

## Part D – Deletion scenario

In your own words (one or two sentences), what would happen if you deleted
`terraform.tfstate` and then ran `terraform plan`?

Terraform would have no record of the existing infrastructure, so it would
plan to create all resources from scratch — VPC, subnets, instance, and buckets —
even though they already exist in LocalStack.
