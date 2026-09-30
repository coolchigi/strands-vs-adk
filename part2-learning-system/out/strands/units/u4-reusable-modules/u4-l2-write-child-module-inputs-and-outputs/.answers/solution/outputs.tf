output "network_subnet_id" {
  description = "Subnet ID from the network module."
  value       = module.network.subnet_id
}

output "compute_instance_id" {
  description = "Instance ID from the compute module."
  value       = module.compute.instance_id
}
