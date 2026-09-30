variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrnetmask(var.vpc_cidr))
    error_message = "The vpc_cidr value must be a valid CIDR block."
  }
}

variable "public_subnet_cidr" {
  type        = string
  description = "CIDR block for the public subnet"
  default     = "10.0.1.0/24"

  validation {
    condition     = can(cidrnetmask(var.public_subnet_cidr))
    error_message = "The public_subnet_cidr value must be a valid CIDR block."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment"
  default     = "dev"
}

variable "instance_types" {
  type        = map(string)
  description = "Instance types per environment"
  default = {
    dev  = "t3.micro"
    prod = "t3.large"
  }
}

variable "extra_tags" {
  type        = map(string)
  description = "Additional tags"
  default     = {}
}
