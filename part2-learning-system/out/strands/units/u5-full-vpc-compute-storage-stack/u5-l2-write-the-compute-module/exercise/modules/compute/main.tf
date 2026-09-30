resource "aws_instance" "app" {
  # TODO: set count = length(var.subnet_ids)
  ami           = "ami-0deadbeef00000000"
  # TODO: use var.instance_type instead of the hard-coded string
  instance_type = "t3.micro"
  # TODO: use var.subnet_ids[count.index] instead of var.subnet_id
  subnet_id     = var.subnet_id
}
