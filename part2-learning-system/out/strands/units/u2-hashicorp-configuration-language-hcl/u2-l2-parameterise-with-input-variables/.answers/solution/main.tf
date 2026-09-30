resource "aws_s3_bucket" "assets" {
  bucket = var.bucket_name
}

resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type

  lifecycle {
    create_before_destroy = true
  }
}
