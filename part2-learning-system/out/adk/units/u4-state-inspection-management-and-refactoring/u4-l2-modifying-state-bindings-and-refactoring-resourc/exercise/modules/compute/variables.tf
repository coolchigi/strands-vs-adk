variable "subnet_id" {
  type        = string
  description = "The subnet ID for the instance"
}

variable "instance_type" {
  type        = string
  description = "The EC2 instance type"
}

variable "environment" {
  type        = string
  description = "The deployment environment name"
}
