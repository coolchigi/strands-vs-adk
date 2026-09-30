# State File Inspection

After running `terraform apply -auto-approve`, open `terraform.tfstate` in a text editor
and answer each question by filling in the blanks below.

## Part A – Resource identity

Find the entry for `aws_subnet.public[0]` in the state file.

- type:     (TODO: copy the value of the "type" key here)
- name:     (TODO: copy the value of the "name" key here)
- provider: (TODO: copy the full value of the "provider" key here)

## Part B – Dependencies

Still on `aws_subnet.public[0]`, find the `dependencies` array inside its instance entry.

- dependencies: (TODO: list every entry in the array here)

Now find the entry for `aws_vpc.main`.

- dependencies: (TODO: list every entry in the array here, or write "empty" if there are none)

## Part C – Cached attribute

Still on `aws_subnet.public[0]`, look inside the `attributes` object.

- cidr_block value in state: (TODO: copy the value here)
- What expression produced it in main.tf? (TODO: write the Terraform expression from main.tf here)

## Part D – Deletion scenario

In your own words (one or two sentences), what would happen if you deleted
`terraform.tfstate` and then ran `terraform plan`?

(TODO: write your answer here)
