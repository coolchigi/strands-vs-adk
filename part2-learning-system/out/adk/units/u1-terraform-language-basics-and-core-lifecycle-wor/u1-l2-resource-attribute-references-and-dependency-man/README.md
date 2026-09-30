# Resource Attribute References and Dependency Management

*Terraform Language Basics and Core Lifecycle Workflow*

## By the end of this lesson you can

- Link infrastructure resources by referencing exported attributes to build implicit dependency graphs
- Define explicit execution order between resources using the depends_on meta-argument

## Where we are

In the previous lesson, we declared the AWS provider and provisioned standalone resources like an Amazon VPC and an S3 bucket. We saw that Terraform tracks each resource block as a target element to be created in your infrastructure.

## The idea

Referencing another managed resource within a resource argument creates an implicit dependency between the two resources ([source](https://developer.hashicorp.com/terraform/language/expressions/references)). Referencing another resource's attribute instructs Terraform to create the upstream dependency first ([source](https://developer.hashicorp.com/terraform/language/block/resource)). When a resource does not use count or for_each, referencing it produces an object whose attributes can be accessed with dot or square-bracket notation ([source](https://developer.hashicorp.com/terraform/language/expressions/references)).

When a resource has the count argument set, referencing it produces a list of objects representing its instances ([source](https://developer.hashicorp.com/terraform/language/expressions/references)). Index syntax can be used to retrieve an attribute of a specific instance of a resource configured with count ([source](https://developer.hashicorp.com/terraform/language/expressions/references)). A splat expression can be used to retrieve a list of an attribute across all instances of a resource configured with count ([source](https://developer.hashicorp.com/terraform/language/expressions/references)). When a resource has the for_each argument set, referencing it produces a map of objects representing its instances ([source](https://developer.hashicorp.com/terraform/language/expressions/references)). Attributes of instances created using for_each are accessed by specifying the instance key using index syntax ([source](https://developer.hashicorp.com/terraform/language/expressions/references)). A data resource is referenced with the data prefix followed by the data source type and name ([source](https://developer.hashicorp.com/terraform/language/expressions/references)).

The depends_on meta-argument explicitly defines an upstream dependency that Terraform must complete operations on before operating on the referencing resource ([source](https://developer.hashicorp.com/terraform/language/block/resource)). In provider blocks, expressions used to configure provider arguments can only reference values known before applying the configuration, such as input variables or direct values, and cannot reference computed resource attributes ([source](https://developer.hashicorp.com/terraform/language/block/provider)).

## Worked example

### Linking Resources and Defining Explicit Dependencies

Suppose we need to deploy an EC2 instance that relies on an S3 bucket policy attachment. The instance configuration does not directly take the attachment's ARN or ID as an argument, but the application running on the instance will crash if the permissions are not active when the instance boots.

#### Step 1: Create an implicit dependency via attribute reference

First, we create a security group and an instance. The instance requires the security group ID, which is computed when the security group is created:

```terraform
resource "aws_security_group" "web" {
  name        = "web-sg"
  description = "Allow HTTP traffic"
  vpc_id      = aws_vpc.main.id
}

resource "aws_instance" "web" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.web.id]
}
```

Because `aws_instance.web` references `aws_security_group.web.id`, Terraform builds a directed acyclic graph (DAG) placing `aws_security_group.web` upstream of `aws_instance.web`. Terraform guarantees the security group is created before provisioning the instance.

#### Step 2: Enforce explicit ordering with `depends_on`

Now suppose we have an `aws_iam_role_policy_attachment` named `s3_access`. Because `aws_instance.web` only takes an instance profile name and has no attribute reference to the policy attachment, Terraform might otherwise attempt to create the instance and the policy attachment concurrently. We add `depends_on` to ensure the attachment finishes first:

```terraform
resource "aws_instance" "web" {
  ami                    = "ami-0c55b159cbfafe1f0"
  instance_type          = "t3.micro"
  vpc_security_group_ids = [aws_security_group.web.id]

  depends_on = [
    aws_iam_role_policy_attachment.s3_access
  ]
}
```

Terraform now enforces that `aws_iam_role_policy_attachment.s3_access` is completely applied before initiating the creation of `aws_instance.web`.

## Your turn

Connect your network components to the VPC created in the previous lesson:

1. In `main.tf`, locate `aws_internet_gateway.gw` and set its `vpc_id` to reference `aws_vpc.main.id`.
2. In `aws_subnet.public`, set its `vpc_id` to reference `aws_vpc.main.id`.
3. In `aws_route_table.public`, set its `vpc_id` to reference `aws_vpc.main.id`.

Notice that `aws_route_table.public` includes `depends_on = [aws_internet_gateway.gw]`. This explicit dependency ensures that the gateway attachment completes before the route table operations execute.

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
