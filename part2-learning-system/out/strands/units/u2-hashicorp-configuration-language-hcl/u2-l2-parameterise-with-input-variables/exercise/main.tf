resource "aws_s3_bucket" "assets" {
  # TODO: replace the hard-coded string with var.bucket_name
  bucket = "tf-learn-assets-bucket"
}

resource "aws_instance" "app" {
  ami           = "ami-0c55b159cbfafe1f0"
  # TODO: replace the hard-coded string with var.instance_type
  instance_type = "t3.micro"

  lifecycle {
    create_before_destroy = true
  }
}
