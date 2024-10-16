terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.0"
    }
  }
}

module "vpc" {
  count = var.create_vpc_network ? 1 : 0
  source  = "terraform-google-modules/network/google"
  version = "~> 9.1"

  project_id   = var.project_id
  network_name = var.vpc_name
  routing_mode = "GLOBAL"

  subnets = []

}


output "vpc_name" {
  value = var.create_vpc_network ? module.vpc[0].network_name : var.vpc_name
  description = "Name of the created VPC network"
}

output "vpc_id" {
  value = module.vpc[0].network_id
  description = "Id of the created VPC network"
}