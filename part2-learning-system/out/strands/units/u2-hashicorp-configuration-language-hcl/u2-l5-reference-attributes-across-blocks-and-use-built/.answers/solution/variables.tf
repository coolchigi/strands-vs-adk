variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket to create"
  default     = "tf-learn-assets-bucket"

  validation {
    condition     = length(var.bucket_name) > 0
    error_message = "bucket_name must not be empty."
  }
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type for the application server"
  default     = "t3.micro"
}

variable "project" {
  type        = string
  description = "Project name used as a tag prefix"
  default     = "myproject"
}

variable "environment" {
  type        = string
  description = "Deployment environment used as a tag suffix"
  default     = "dev"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones"
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}
