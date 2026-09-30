# TODO: replace subnet_id with three variables:
#   ami_id        - string, required, description: "AMI ID to use for each EC2 instance."
#   subnet_ids    - list(string), required, description: "List of subnet IDs; one instance is created in each subnet."
#   instance_type - string, default "t3.micro", description: "EC2 instance type for every instance in the module."
variable "subnet_id" {
  type        = string
  description = "ID of the subnet to place the instance in."
}
