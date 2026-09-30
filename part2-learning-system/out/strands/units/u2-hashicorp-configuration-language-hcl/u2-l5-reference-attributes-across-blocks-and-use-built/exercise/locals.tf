locals {
  name_prefix = "${var.project}-${var.environment}"
  # TODO: add subnet_count = length(var.availability_zones)
}
