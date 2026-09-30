resource "aws_s3_bucket" "assets" {
  bucket = "tf-learn-assets-bucket"
}

resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t3.micro"

  lifecycle {
    create_before_destroy = true
  }
}
