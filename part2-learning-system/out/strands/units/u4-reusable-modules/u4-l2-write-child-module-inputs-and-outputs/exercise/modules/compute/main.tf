resource "aws_instance" "app" {
  ami           = "ami-0deadbeef00000000"
  instance_type = "t3.micro"
  # TODO: set subnet_id = var.subnet_id
}
