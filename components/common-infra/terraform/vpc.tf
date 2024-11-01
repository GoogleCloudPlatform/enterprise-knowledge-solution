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

}

resource "google_dns_policy" "dns-policy" {
  name           = "dns-policy"
  enable_logging = true

  networks {
    network_url = module.vpc[0].network_id
  }
}

module "network_firewall_policy" {

  source      = "github.com/terraform-google-modules/terraform-google-network.git//modules/network-firewall-policy?ref=7957e51850e248ca09b02fb445a6e56ac7a0e58c" #commit hash of version 9.3.0
  project_id  = var.project_id
  policy_name = "firewall-policy"
  description = "firewall policy to enable EKS functionality"
  target_vpcs = [module.vpc[0].network_id]

  rules = [
    {
      priority       = "1000"
      direction      = "EGRESS"
      action         = "allow"
      rule_name      = "allow-google-apis-restricted-vip"
      description    = "Allow private HTTPS access to google apis on the restricted VIP"
      enable_logging = true
      match = {
        dest_ip_ranges = ["199.36.153.4/30"]
        layer4_configs = [
          {
            ip_protocol = "tcp"
            ports       = ["443"]
          },
        ]
      }
    },
    {
      priority       = "65530"
      direction      = "EGRESS"
      action         = "deny"
      rule_name      = "default-deny-egress"
      description    = "low priority catch-all to block egress traffic unless explicitly allowed by another rule"
      enable_logging = true
      match = {
        dest_ip_ranges = ["0.0.0.0/0"]
        layer4_configs = [
          {
            ip_protocol = "all"
          },
        ]
      }
    },
  ]
}

module "dns-private-zone" {
  source     = "github.com/terraform-google-modules/terraform-google-cloud-dns?ref=92bd8140d059388c6c22742ffcb5f4ab2c24cee9" #commit hash of version 5.3.0
  project_id = "var.project_id"
  type       = "private"
  name       = "googleapis.com"
  domain     = "googleapis.com."

  private_visibility_config_networks = [module.vpc[0].network_self_link]

  recordsets = [
    {
      name = "restricted.googleapis.com."
      type = "A"
      ttl  = 300
      records = [
        "199.36.153.4", "199.36.153.5", "199.36.153.6", "199.36.153.7",
      ]
    },
    {
      name = "*.googleapis.com."
      type = "CNAME"
      ttl  = 300
      records = [
        "restricted.googleapis.com",
      ]
    },
  ]
}
