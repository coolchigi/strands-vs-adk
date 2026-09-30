module "network" {
  source   = "./modules/network"
  vpc_cidr = "10.0.0.0/16"
}

module "compute" {
  source    = "./modules/compute"
  subnet_id = module.network.subnet_id
}

module "storage" {
  for_each = toset(["my-project-assets", "my-project-logs"])

  source      = "./modules/storage"
  bucket_name = each.key
}
