variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"

  # TODO: Add validation block ensuring var.vpc_cidr is valid using can(cidrnetmask(var.vpc_cidr))
}

variable "public_subnet_cidr" {
  type        = string
  description = "CIDR block for the public subnet"
  default     = "10.0.1.0/24"

  # TODO: Add validation block ensuring var.public_subnet_cidr is valid using can(cidrnetmask(var.public_subnet_cidr))
}
