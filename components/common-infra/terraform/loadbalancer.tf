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
locals {
  eks_label = {
    goog-packaged-solution : "eks-solution"
  }
}

module "eks_webui_lb" {
  source                          = "github.com/terraform-google-modules/terraform-google-lb-http.git//modules/serverless_negs?ref=99d56bea9a7f561102d2e449852eaf725e8b8d0c" # version 12.0.0
  name                            = "${var.webui_service_name}-lb"
  project                         = var.project_id
  managed_ssl_certificate_domains = var.webui_domains
  load_balancing_scheme           = "EXTERNAL_MANAGED"
  ssl                             = true
  ssl_policy                      = google_compute_ssl_policy.ssl-policy.self_link
  https_redirect                  = true
  create_url_map                  = false
  url_map                         = google_compute_url_map.urlmap.id
  labels                          = local.eks_label

  backends = {
    backend-query = {
      description = "backend for document search user interface"
      groups = [
        {
          group = var.neg_id_query
        }
      ]
      enable_cdn = false

      iap_config = {
        enable               = true
        oauth2_client_id     = google_iap_client.project_client.client_id
        oauth2_client_secret = google_iap_client.project_client.secret
      }
      log_config = {
        enable = true
      }
    },

    backend-hitl = {
      description = "backend for HITL user interface"
      groups = [
        {
          group = var.neg_id_hitl
        }
      ]
      enable_cdn = false
      iap_config = {
        enable               = true
        oauth2_client_id     = google_iap_client.project_client.client_id
        oauth2_client_secret = google_iap_client.project_client.secret
      }
      log_config = {
        enable = true
      }
    },

    backend-hitl-api = {
      description = "backend for HITL API"
      groups = [
        {
          group = var.neg_id_hitl_api
        }
      ]
      enable_cdn = false
      iap_config = {
        enable               = true
        oauth2_client_id     = google_iap_client.project_client.client_id
        oauth2_client_secret = google_iap_client.project_client.secret
      }
      log_config = {
        enable = true
      }
    }
  }
}

resource "google_compute_url_map" "urlmap" {
  name            = "${var.webui_service_name}-urlmap"
  description     = "Load balancer in front of various Cloud Run Services that act as different UI components of EKS"
  project         = var.project_id
  default_service = module.eks_webui_lb.backend_services["backend-query"].id
  host_rule {
    hosts        = [var.webui_domains[0]]
    path_matcher = "eks-webui"
  }
  path_matcher {
    name            = "eks-webui"
    default_service = module.eks_webui_lb.backend_services["backend-query"].id
    path_rule {
      paths   = ["/query"]
      service = module.eks_webui_lb.backend_services["backend-query"].id
    }
    path_rule {
      paths   = ["/hitl"]
      service = module.eks_webui_lb.backend_services["backend-hitl"].id
    }
    path_rule {
      paths   = ["/hitl-api"]
      service = module.eks_webui_lb.backend_services["backend-hitl-api"].id
    }
  }
}
