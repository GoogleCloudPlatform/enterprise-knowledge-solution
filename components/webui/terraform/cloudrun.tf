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

module "cloud_run_web_account" {
  source     = "github.com/terraform-google-modules/terraform-google-service-accounts?ref=a11d4127eab9b51ec9c9afdaf51b902cd2c240d9" #commit hash of version 4.0.0
  project_id = var.project_id
  names      = ["cloud-run-web"]
  project_roles = [
    "${var.project_id}=>roles/aiplatform.user",
    "${var.project_id}=>roles/discoveryengine.viewer",
    "${var.project_id}=>roles/storage.objectUser",
  ]
  display_name = "EKS Cloud Run WebUI Service Account"
  description  = "specific custom service account for Web APP"
}

resource "null_resource" "deployment_trigger" {
  triggers = {
    source_contents_hash = local.cloud_build_content_hash
  }
}

resource "google_cloud_run_v2_service" "eks_webui" {
  name                = var.webui_service_name
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  template {
    scaling {
      max_instance_count = 2
    }
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo}/${var.webui_service_name}:latest"
      ports {
        container_port = 8080
      }
      env {
        name  = "PROJECT_ID"
        value = module.project_services.project_id
      }
      env {
        name  = "AGENT_BUILDER_LOCATION"
        value = var.vertex_ai_data_store_region
      }
      env {
        name  = "AGENT_BUILDER_DATA_STORE_ID"
        value = var.agent_builder_data_store_id
      }
      env {
        name  = "AGENT_BUILDER_SEARCH_ID"
        value = var.agent_builder_search_id
      }
      resources {
        limits = {
          cpu    = "2"
          memory = "1024Mi"
        }
      }
    }
    service_account = module.cloud_run_web_account.email
  }
  lifecycle {
    replace_triggered_by = [null_resource.deployment_trigger]
  }
  depends_on = [
    module.gcloud_build_web_ui_app.wait
  ]
}

resource "google_compute_region_network_endpoint_group" "eks_webui_neg" {
  name                  = "${var.webui_service_name}-query-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.eks_webui.name
  }
  lifecycle {
    replace_triggered_by = [google_cloud_run_v2_service.eks_webui]
  }
}

resource "google_compute_region_network_endpoint_group" "stub" {
  name                  = "${var.webui_service_name}-stub-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  project               = var.project_id
  cloud_run {
    service = google_cloud_run_v2_service.cloudrunservice2.name
  }
}

module "eks_webui_lb" {
  source                          = "github.com/terraform-google-modules/terraform-google-lb-http.git//modules/serverless_negs?ref=99d56bea9a7f561102d2e449852eaf725e8b8d0c" # version 12.0.0
  name                            = "${var.webui_service_name}-lb"
  project                         = var.project_id
  managed_ssl_certificate_domains = var.lb_ssl_certificate_domains
  load_balancing_scheme           = "EXTERNAL_MANAGED"
  ssl                             = true
  ssl_policy                      = var.ssl_policy_link
  https_redirect                  = true
  create_url_map                  = false
  url_map                         = google_compute_url_map.urlmap.id
  labels                          = local.eks_label

  backends = {
    backend1 = {
      description = "backend for query user interface"
      groups = [
        {
          group = google_compute_region_network_endpoint_group.eks_webui_neg.id
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
    },

    backend2 = {
      description = "backend for HITL user interface"
      groups = [
        {
          group = google_compute_region_network_endpoint_group.stub.id
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

resource "google_compute_url_map" "urlmap" {
  name        = "${var.webui_service_name}-urlmap"
  description = "Load balancer in front of various Cloud Run Services that act as different UI components of EKS"
  project     = var.project_id

  default_service = module.eks_webui_lb.backend_services["backend1"].id

  host_rule {
    hosts        = [var.lb_ssl_certificate_domains[0]]
    path_matcher = "mysite"
  }

  path_matcher {
    name            = "mysite"
    default_service = module.eks_webui_lb.backend_services["backend1"].id

    path_rule {
      paths   = ["/"]
      service = module.eks_webui_lb.backend_services["backend1"].id
    }

    path_rule {
      paths   = ["/hitl"]
      service = module.eks_webui_lb.backend_services["backend2"].id
    }
  }

}

data "google_iam_policy" "webui_policy" {
  binding {
    role    = "roles/run.invoker"
    members = setunion(var.iap_access_domains, [var.iap_member])
  }
}

resource "google_cloud_run_v2_service_iam_policy" "policy1" {
  project     = google_cloud_run_v2_service.eks_webui.project
  location    = google_cloud_run_v2_service.eks_webui.location
  name        = google_cloud_run_v2_service.eks_webui.name
  policy_data = data.google_iam_policy.webui_policy.policy_data
}

resource "google_cloud_run_v2_service_iam_policy" "policy2" {
  project     = google_cloud_run_v2_service.cloudrunservice2.project
  location    = google_cloud_run_v2_service.cloudrunservice2.location
  name        = google_cloud_run_v2_service.cloudrunservice2.name
  policy_data = data.google_iam_policy.webui_policy.policy_data
}

resource "google_cloud_run_v2_service" "cloudrunservice2" {
  name                = "stub-for-hitl"
  location            = var.region
  deletion_protection = false
  project             = var.project_id
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  template {
    containers {
      image = "us-docker.pkg.dev/cloudrun/container/hello"
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
    service_account = module.cloud_run_web_account.email
  }
}
