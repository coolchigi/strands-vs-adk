module "network" {
  source   = "./modules/network"
  vpc_cidr = "10.0.0.0/16"
}

module "compute" {
  source    = "./modules/compute"
  subnet_id = module.network.subnet_id
}

# TODO: Replace this comment with a single module block named "storage"
# that uses for_each over toset(["my-project-assets", "my-project-logs"])
# and passes each.key as bucket_name.
