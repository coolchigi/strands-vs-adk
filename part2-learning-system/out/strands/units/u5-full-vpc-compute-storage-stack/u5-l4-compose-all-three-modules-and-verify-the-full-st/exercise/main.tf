# TODO: Call module "networking" from ./modules/networking
#       with vpc_cidr = "10.0.0.0/16" and
#       availability_zones = ["us-east-1a", "us-east-1b"]

# TODO: Call module "compute" from ./modules/compute
#       with ami_id = "ami-0c55b159cbfafe1f0" and
#       subnet_ids threaded from module.networking.subnet_ids

# TODO: Call module "storage" from ./modules/storage
#       using for_each over toset(["my-project-assets", "my-project-logs"])
#       with bucket_name = each.key
