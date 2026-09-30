locals {
  name_prefix  = "${var.project}-${var.environment}"
  subnet_count = length(var.availability_zones)
}
