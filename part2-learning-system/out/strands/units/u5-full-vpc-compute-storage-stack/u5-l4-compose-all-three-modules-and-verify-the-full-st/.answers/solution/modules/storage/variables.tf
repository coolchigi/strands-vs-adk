variable "bucket_name" {
  type        = string
  description = "Name of the S3 bucket to create."
}

variable "tags" {
  type        = map(string)
  description = "Tags to set on the bucket."
  default     = {}
}
