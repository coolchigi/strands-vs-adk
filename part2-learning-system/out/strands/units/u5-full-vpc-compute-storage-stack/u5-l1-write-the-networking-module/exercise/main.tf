module "networking" {
  source = "./modules/networking"

  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b"]
}

module "compute" {
  source    = "./modules/compute"
  subnet_id = module.networking.subnet_ids[0]
}

module "storage" {
  for_each = toset(["my-project-assets", "my-project-logs"])

  source      = "./modules/storage"
  bucket_name = each.key
}
