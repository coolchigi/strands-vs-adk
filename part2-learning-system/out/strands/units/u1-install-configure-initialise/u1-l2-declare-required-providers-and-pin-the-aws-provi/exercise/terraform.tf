terraform {
  # TODO: set required_version to ">= 1.1.0"

  required_providers {
    aws = {
      source = "hashicorp/aws"
      # TODO: add version constraint ~> 6.0
    }
  }
}
