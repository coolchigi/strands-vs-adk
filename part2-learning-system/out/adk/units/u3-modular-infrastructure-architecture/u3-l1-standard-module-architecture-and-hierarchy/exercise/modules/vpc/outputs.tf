output "vpc_id" {
  description = "The ID of the VPC"
  value       = "" # TODO: Export aws_vpc.main.id
}

output "public_subnet_id" {
  description = "The ID of the public subnet"
  value       = "" # TODO: Export aws_subnet.public.id
}
