module "networking" {
  source = "./modules/networking"

  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
}

module "compute" {
  source = "./modules/compute"

  ami_id     = "ami-0c55b159cbfafe1f0"
  subnet_ids = module.networking.subnet_ids
}

module "storage" {
  for_each = toset(["my-project-assets", "my-project-logs"])

  source      = "./modules/storage"
  bucket_name = each.key
}
