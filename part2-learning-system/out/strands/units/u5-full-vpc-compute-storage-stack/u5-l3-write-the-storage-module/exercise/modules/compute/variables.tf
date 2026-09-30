variable "ami_id" {
  type        = string
  description = "AMI ID to use for each EC2 instance."
}

variable "subnet_ids" {
  type        = list(string)
  description = "List of subnet IDs; one instance is created in each subnet."
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for every instance in the module."
  default     = "t3.micro"
}
