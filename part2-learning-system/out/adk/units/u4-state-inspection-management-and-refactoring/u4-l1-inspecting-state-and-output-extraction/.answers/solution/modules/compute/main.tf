resource "aws_instance" "web" {
  ami           = "ami-12345678"
  subnet_id     = var.subnet_id
  instance_type = var.instance_type

  tags = {
    Name        = "${var.environment}-web"
    Environment = var.environment
  }
}
