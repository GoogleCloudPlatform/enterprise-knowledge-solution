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


module "cloud_run_web_account" {
  source     = "github.com/terraform-google-modules/terraform-google-service-accounts?ref=a11d4127eab9b51ec9c9afdaf51b902cd2c240d9" #commit hash of version 4.0.0
  project_id = var.project_id
  names      = ["cloud-run-adp-api"]
  project_roles = [
    "${var.project_id}=>roles/aiplatform.user",
    "${var.project_id}=>roles/discoveryengine.viewer",
    "${var.project_id}=>roles/storage.objectUser",
  ]
  display_name = "EKS Cloud Run adpapi Service Account"
  description  = "specific custom service account for Web APP"
}

resource "null_resource" "deployment_trigger" {
  triggers = {
    source_contents_hash = local.cloud_build_content_hash
  }
}

resource "google_cloud_run_v2_service" "eks_adpapi" {
  name                = var.adpapi_service_name
  location            = var.region
  deletion_protection = false
  ingress             = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"
  template {
    scaling {
      max_instance_count = 2
    }
    vpc_access {
      network_interfaces {
        network    = var.vpc_network_name
        subnetwork = var.serverless_connector_subnet
      }
      egress = "ALL_TRAFFIC"
    }
    containers {
      #image = "${var.region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo}/${var.adpapi_service_name}:latest"
      image = "us-docker.pkg.dev/cloudrun/container/hello"
      ports {
        container_port = 8080
      }
      env {
        name  = "PROJECT_ID"
        value = module.project_services.project_id
      }
      env {
        name  = "UI_URL"
        value = var.adp_ui_url
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
    module.gcloud_build_apd_api_app.wait
  ]
}

resource "google_compute_region_network_endpoint_group" "eks_adpapi_neg" {
  name                  = "${var.adpapi_service_name}-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region
  cloud_run {
    service = google_cloud_run_v2_service.eks_adpapi.name
  }
  lifecycle {
    replace_triggered_by = [google_cloud_run_v2_service.eks_adpapi]
  }
}

data "google_iam_policy" "adpapi_policy" {
  binding {
    role    = "roles/run.invoker"
    members = [var.iap_member]
    #members = setunion(var.iap_access_domains, [var.iap_member])
  }
}

resource "google_cloud_run_v2_service_iam_policy" "policy" {
  project     = google_cloud_run_v2_service.eks_adpapi.project
  location    = google_cloud_run_v2_service.eks_adpapi.location
  name        = google_cloud_run_v2_service.eks_adpapi.name
  policy_data = data.google_iam_policy.adpapi_policy.policy_data
}
