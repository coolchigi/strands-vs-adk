mock_provider "aws" {}

run "s3_bucket_exists" {
  command = apply

  assert {
    condition     = aws_s3_bucket.assets.bucket == "tf-learn-assets-bucket"
    error_message = "aws_s3_bucket.assets must have bucket = \"tf-learn-assets-bucket\"."
  }
}

run "ec2_instance_has_ami" {
  command = apply

  assert {
    condition     = aws_instance.app.ami == "ami-0c55b159cbfafe1f0"
    error_message = "aws_instance.app must have ami = \"ami-0c55b159cbfafe1f0\"."
  }
}

run "ec2_instance_has_instance_type" {
  command = apply

  assert {
    condition     = aws_instance.app.instance_type == "t3.micro"
    error_message = "aws_instance.app must have instance_type = \"t3.micro\"."
  }
}
