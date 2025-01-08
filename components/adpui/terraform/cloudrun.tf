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

module "cloud_run_adp_account" {
  source     = "github.com/terraform-google-modules/terraform-google-service-accounts?ref=a11d4127eab9b51ec9c9afdaf51b902cd2c240d9" #commit hash of version 4.0.0
  project_id = var.project_id
  names      = ["cloud-run-adp"]
  project_roles = [
    "${var.project_id}=>roles/storage.objectUser",
  ]
  display_name = "EKS Cloud Run ADP UI Service Account"
  description  = "specific custom service account for ADP Web App"
}

resource "null_resource" "deployment_trigger" {
  triggers = {
    source_contents_hash = local.cloud_build_content_hash
  }
}

resource "google_cloud_run_v2_service" "eks_adpui" {
  name                = var.adpui_service_name
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  template {
    scaling {
      max_instance_count = 2
    }
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo}/${var.adpui_service_name}:latest"
      ports {
        container_port = 8080
      }
      resources {
        limits = {
          cpu    = "2"
          memory = "1024Mi"
        }
      }
    }
    service_account = module.cloud_run_adp_account.email
  }
  lifecycle {
    replace_triggered_by = [null_resource.deployment_trigger]
  }
  depends_on = [
    module.gcloud_build_adp_ui_app.wait
  ]
}

resource "google_compute_region_network_endpoint_group" "eks_adpui_neg" {
  name                  = "${var.adpui_service_name}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.eks_adpui.name
  }
  lifecycle {
    replace_triggered_by = [google_cloud_run_v2_service.eks_adpui]
  }
}

module "eks_adpui_lb" {
  source                          = "github.com/terraform-google-modules/terraform-google-lb-http.git//modules/serverless_negs?ref=99d56bea9a7f561102d2e449852eaf725e8b8d0c" # version 12.0.0
  name                            = "${var.adpui_service_name}-lb"
  project                         = var.project_id
  managed_ssl_certificate_domains = var.lb_ssl_certificate_domains
  ssl                             = true
  ssl_policy                      = var.ssl_policy_link
  https_redirect                  = true
  labels                          = local.eks_label

  backends = {
    default = {
      description = null
      groups = [
        {
          group = google_compute_region_network_endpoint_group.eks_adpui_neg.id
        }
      ]
      enable_cdn = false

      iap_config = {
        enable               = true
        oauth2_client_id     = var.iap_client_id
        oauth2_client_secret = var.iap_secret
      }
      log_config = {
        enable = true
      }
    }
  }
}

data "google_iam_policy" "adpui_policy" {
  binding {
    role    = "roles/run.invoker"
    members = setunion(var.iap_access_domains, [var.iap_member])
  }
}

resource "google_cloud_run_v2_service_iam_policy" "policy" {
  project     = google_cloud_run_v2_service.eks_adpui.project
  location    = google_cloud_run_v2_service.eks_adpui.location
  name        = google_cloud_run_v2_service.eks_adpui.name
  policy_data = data.google_iam_policy.adpui_policy.policy_data
}
