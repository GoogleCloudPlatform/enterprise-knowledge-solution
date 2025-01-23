# Copyright 2024 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

module "vpc" {
  count        = var.create_vpc_network ? 1 : 0
  source       = "github.com/terraform-google-modules/terraform-google-network?ref=2477e469c9734638c9ed83e69fe8822452dacbc6" #commit hash of version 9.2.0
  project_id   = module.project_services.project_id
  network_name = var.vpc_name
  routing_mode = "GLOBAL"

  subnets = []

  depends_on = [module.project_services]

}

data "google_compute_network" "provided_vpc" {
  count = var.create_vpc_network ? 0 : 1
  name  = var.vpc_name
}

locals {
  vpc_network_id        = var.create_vpc_network ? module.vpc[0].network_id : data.google_compute_network.provided_vpc[0].id
  vpc_network_self_link = var.create_vpc_network ? module.vpc[0].network_self_link : data.google_compute_network.provided_vpc[0].self_link
  vpc_network_name      = var.create_vpc_network ? module.vpc[0].network_name : data.google_compute_network.provided_vpc[0].name
}

resource "google_dns_policy" "dns-policy" {
  count          = var.create_vpc_network ? 1 : 0
  name           = "dns-policy"
  enable_logging = true

  networks {
    network_url = local.vpc_network_id
  }
}

resource "google_compute_network_firewall_policy" "policy" {
  count       = var.create_vpc_network ? 1 : 0
  name        = "network-firewall-policy"
  description = "firewall policy to enable EKS functionality"
}

resource "google_compute_network_firewall_policy_association" "association" {
  count             = var.create_vpc_network ? 1 : 0
  name              = "association"
  attachment_target = local.vpc_network_id
  firewall_policy   = google_compute_network_firewall_policy.policy[0].name
}

resource "google_compute_network_firewall_policy_rule" "allow-google-apis" {
  count           = var.create_vpc_network ? 1 : 0
  description     = "Allow private HTTPS access to google apis on the private VIP"
  action          = "allow"
  direction       = "EGRESS"
  enable_logging  = true
  firewall_policy = google_compute_network_firewall_policy.policy[0].name
  priority        = 1000
  rule_name       = "allow-google-apis-private-vip"

  match {
    dest_ip_ranges = ["199.36.153.4/30"]
    layer4_configs {
      ip_protocol = "tcp"
      ports       = ["443"]
    }
  }
}

resource "google_compute_network_firewall_policy_rule" "allow-psa-to-alloydb" {
  count           = var.create_vpc_network ? 1 : 0
  description     = "Allow egress to PSA reserved range used for AlloyDB"
  action          = "allow"
  direction       = "EGRESS"
  enable_logging  = true
  firewall_policy = google_compute_network_firewall_policy.policy[0].name
  priority        = 1010
  rule_name       = "allow-psa-to-alloydb"

  match {
    dest_ip_ranges = ["${var.psa_reserved_address}/24"]
    layer4_configs {
      ip_protocol = "tcp"
      ports       = ["5433"]
    }
  }
}

resource "google_compute_network_firewall_policy_rule" "allow-google-apis-directpath" {
  count           = var.create_vpc_network ? 1 : 0
  description     = "Allow private HTTPS access to google services that bypass GFE (Composer 3)"
  action          = "allow"
  direction       = "EGRESS"
  enable_logging  = true
  firewall_policy = google_compute_network_firewall_policy.policy[0].name
  priority        = 1020
  rule_name       = "allow-google-apis-directpath"

  match {
    dest_ip_ranges = ["34.126.0.0/18"]
    layer4_configs {
      ip_protocol = "tcp"
    }
  }
}

resource "google_compute_network_firewall_policy_rule" "default-deny" {
  count           = var.create_vpc_network ? 1 : 0
  description     = "Low priority rule to deny all egress not explicitly matched by other rules"
  action          = "deny"
  direction       = "EGRESS"
  enable_logging  = true
  firewall_policy = google_compute_network_firewall_policy.policy[0].name
  priority        = 65535
  rule_name       = "default-deny-all"

  match {
    dest_ip_ranges = ["0.0.0.0/0"]
    layer4_configs {
      ip_protocol = "all"
    }
  }
}

module "dns-private-zone-googleapis" {
  count      = var.create_vpc_network ? 1 : 0
  source     = "github.com/terraform-google-modules/terraform-google-cloud-dns?ref=92bd8140d059388c6c22742ffcb5f4ab2c24cee9" #commit hash of version 5.3.0
  project_id = var.project_id
  type       = "private"
  name       = "googleapis-com"
  domain     = "googleapis.com."

  private_visibility_config_networks = [local.vpc_network_self_link]

  recordsets = [
    {
      name = "restricted"
      type = "A"
      ttl  = 300
      records = [
        "199.36.153.4", "199.36.153.5", "199.36.153.6", "199.36.153.7",
      ]
    },
    {
      name = "*"
      type = "CNAME"
      ttl  = 300
      records = [
        "restricted.googleapis.com.",
      ]
    },
  ]
}
