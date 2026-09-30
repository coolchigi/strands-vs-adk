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
