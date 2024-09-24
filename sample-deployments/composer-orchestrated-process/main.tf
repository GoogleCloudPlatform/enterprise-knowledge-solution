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
provider "google" {
  project               = var.project_id
  user_project_override = true
  billing_project       = var.project_id
  default_labels        = local.dpu_label
}

locals {
  processing_cloud_run_job_name  = "doc-processor"
  form_parser_cloud_run_job_name = "form-parser"
  classifier_cloud_run_job_name  = "doc-classifier"
  dpu_label = {
    goog-packaged-solution : "eks-solution"
  }
}

module "common_infra" {
  source     = "../../components/common-infra/terraform"
  project_id = var.project_id
  region     = var.region
}

module "project_services" {
  source                      = "github.com/terraform-google-modules/terraform-google-project-factory.git//modules/project_services?ref=ff00ab5032e7f520eb3961f133966c6ced4fd5ee" # commit hash of version 17.0.0
  project_id                  = var.project_id
  disable_services_on_destroy = false
  disable_dependent_services  = false
  activate_apis = [
    "cloudresourcemanager.googleapis.com",
    "serviceusage.googleapis.com",
    "iam.googleapis.com",
    "aiplatform.googleapis.com",
    "discoveryengine.googleapis.com"
  ]
}

resource "google_discovery_engine_data_store" "dpu_ds" {
  project                     = module.project_services.project_id
  location                    = var.vertex_ai_data_store_region
  data_store_id               = "dpu-doc-store"
  display_name                = "Document Processing & Understanding"
  industry_vertical           = "GENERIC"
  content_config              = "CONTENT_REQUIRED"
  solution_types              = ["SOLUTION_TYPE_SEARCH"]
  create_advanced_site_search = false
}

resource "google_discovery_engine_search_engine" "basic" {
  project = module.project_services.project_id
  # TODO: Change this
  engine_id      = module.project_services.project_id
  collection_id  = "default_collection"
  location       = var.vertex_ai_data_store_region
  display_name   = "Example Display Name"
  data_store_ids = [google_discovery_engine_data_store.dpu_ds.data_store_id]
  search_engine_config {
    search_tier    = "SEARCH_TIER_ENTERPRISE"
    search_add_ons = ["SEARCH_ADD_ON_LLM"]
  }
}

module "processor" {
  source     = "../../components/processing/terraform"
  project_id = var.project_id
  region     = var.region
  # bq_region                         = var.region
  # gcs_region                        = var.region
  repository_region                 = var.region
  artifact_repo                     = module.common_infra.artifact_repo.name
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
  processing_cloud_run_job_name     = local.processing_cloud_run_job_name
}

module "form_parser_processor" {
  source                         = "../../components/processing/form_parser/deployment"
  project_id                     = var.project_id
  region                         = var.region
  location                       = var.docai_location
  gcs_input_prefix               = module.common_infra.gcs_process_bucket_name
  gcs_output_prefix              = module.common_infra.gcs_process_bucket_name
  form_parser_cloud_run_job_name = local.form_parser_cloud_run_job_name
  alloydb_cluster_name           = module.common_infra.alloydb_cluster_name
}

module "doc_classifier_job" {
  source     = "../../components/doc-classifier/terraform"
  project_id = var.project_id
  region     = var.region
  # repository_region                 = var.region
  artifact_repo = module.common_infra.artifact_repo.name
  # cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
  classifier_cloud_run_job_name = local.classifier_cloud_run_job_name

}

module "dpu_workflow" {
  source           = "../../components/dpu-workflow/terraform"
  region           = var.region
  project_id       = var.project_id
  vpc_network_name = module.common_infra.vpc_network_name
  vpc_network_id   = module.common_infra.vpc_network_id
  composer_env_variables = {
    DPU_OUTPUT_DATASET      = module.common_infra.bq_store_dataset_id
    DPU_INPUT_BUCKET        = module.common_infra.gcs_input_bucket_name
    DPU_PROCESS_BUCKET      = module.common_infra.gcs_process_bucket_name
    DPU_REJECT_BUCKET       = module.common_infra.gcs_reject_bucket_name
    DPU_REGION              = var.region
    DPU_DATA_STORE_REGION   = var.vertex_ai_data_store_region
    DOC_PROCESSOR_JOB_NAME  = module.processor.processing_cloud_run_job_name
    DPU_DATA_STORE_ID       = google_discovery_engine_data_store.dpu_ds.data_store_id
    FORMS_PARSER_JOB_NAME   = module.form_parser_processor.form_parser_cloud_run_job_name
    DOC_CLASSIFIER_JOB_NAME = module.doc_classifier_job.classifier_cloud_run_job_name
  }
}

module "dpu_ui" {
  source                      = "../../components/webui/terraform"
  project_id                  = var.project_id
  region                      = var.region
  artifact_repo               = module.common_infra.artifact_repo.name
  iap_access_domains          = var.iap_access_domains
  vertex_ai_data_store_region = var.vertex_ai_data_store_region
  agent_builder_data_store_id = google_discovery_engine_data_store.dpu_ds.data_store_id
  agent_builder_search_id     = google_discovery_engine_search_engine.basic.engine_id
  webui_service_name          = var.webui_service_name
  lb_ssl_certificate_domains  = var.webui_domains
}

# Depends on: input bucket, artefactory (registury_url), and docprocessor service account
resource "local_file" "env_file" {
  filename = "${path.module}/../../.env"
  content = templatefile("${path.module}/env.template", {

    # Common infrastructure
    project_id         = var.project_id,
    region             = var.region,
    bq_region          = var.region,
    gcs_region         = var.region,
    repository_region  = var.region,
    artifact_repo      = module.common_infra.artifact_repo.name
    gcs_input_bucket   = module.common_infra.gcs_input_bucket_name
    gcs_process_bucket = module.common_infra.gcs_process_bucket_name
    gcs_reject_bucket  = module.common_infra.gcs_reject_bucket_name

    # Cloud run specific..
    processing_cloud_run_job_name = local.processing_cloud_run_job_name
    processing_service_account    = module.processor.doc_processor_service_account

    form_parser_cloud_run_job_name = local.form_parser_cloud_run_job_name
    form_parser_service_account    = module.form_parser_processor.form_parser_service_account

    classifier_cloud_run_job_name = local.classifier_cloud_run_job_name
    classifier_service_account    = module.doc_classifier_job.classifier_service_account

    # Agent builder
    agent_builder_location      = var.vertex_ai_data_store_region
    agent_builder_data_store_id = google_discovery_engine_data_store.dpu_ds.data_store_id
    agent_builder_search_id     = google_discovery_engine_search_engine.basic.engine_id
  })
}
