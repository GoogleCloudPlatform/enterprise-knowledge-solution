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
  processing_cloud_run_job_name = "ms-office-doc-processor"
  classifier_cloud_run_job_name = "doc-classifier"
  dpu_label = {
    goog-packaged-solution : "eks-solution"
  }
}

module "common_infra" {
  source                            = "../../components/common-infra/terraform"
  project_id                        = var.project_id
  region                            = var.region
  create_vpc_network                = var.create_vpc_network
  vpc_name                          = var.vpc_name
  serverless_connector_subnet       = var.serverless_connector_subnet
  serverless_connector_subnet_range = var.serverless_connector_subnet_range
  psa_reserved_address              = var.psa_reserved_address
  composer_cidr                     = var.composer_cidr
  iap_access_domains                = var.iap_access_domains
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
  data_store_id               = "eks-data-store"
  display_name                = "Enterprise Knowledge Store"
  industry_vertical           = "GENERIC"
  content_config              = "CONTENT_REQUIRED"
  solution_types              = ["SOLUTION_TYPE_SEARCH"]
  create_advanced_site_search = false
  document_processing_config {
    default_parsing_config {
      layout_parsing_config {}
    }
  }
}

resource "google_discovery_engine_search_engine" "basic" {
  project = module.project_services.project_id
  # TODO: Change this
  engine_id      = "ent-search-agent"
  collection_id  = "default_collection"
  location       = var.vertex_ai_data_store_region
  display_name   = "Enterprise Search Agent"
  data_store_ids = [google_discovery_engine_data_store.dpu_ds.data_store_id]
  search_engine_config {
    search_tier    = "SEARCH_TIER_ENTERPRISE"
    search_add_ons = ["SEARCH_ADD_ON_LLM"]
  }
}

module "processor" {
  source                            = "../../components/processing/terraform"
  project_id                        = var.project_id
  region                            = var.region
  repository_region                 = var.region
  artifact_repo                     = module.common_infra.artifact_repo.name
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
  processing_cloud_run_job_name     = local.processing_cloud_run_job_name
}

module "doc_classifier_job" {
  source                            = "../../components/doc-classifier/terraform"
  project_id                        = var.project_id
  region                            = var.region
  artifact_repo                     = module.common_infra.artifact_repo.name
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
  classifier_cloud_run_job_name     = local.classifier_cloud_run_job_name
}

module "specialized_parser_job" {
  source                            = "../../components/specialized-parser/terraform"
  project_id                        = var.project_id
  region                            = var.region
  processors_location               = var.docai_location
  artifact_repo                     = module.common_infra.artifact_repo.name
  bigquery_dataset_id               = module.common_infra.bq_store_dataset_id
  alloydb_instance                  = module.common_infra.alloydb_primary_instance
  alloydb_cluster                   = module.common_infra.alloydb_cluster_name
  network                           = module.common_infra.vpc_network_name
  serverless_connector_subnet       = module.common_infra.serverless_connector_subnet
  alloydb_cluster_ready             = module.common_infra.alloydb_cluster_ready
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
}

module "dpu_workflow" {
  source           = "../../components/dpu-workflow/terraform"
  region           = var.region
  project_id       = var.project_id
  vpc_network_name = module.common_infra.vpc_network_name
  vpc_network_id   = module.common_infra.vpc_network_id
  composer_cidr    = var.composer_cidr
  composer_env_variables = {
    DPU_OUTPUT_DATASET              = module.common_infra.bq_store_dataset_id
    DPU_INPUT_BUCKET                = module.common_infra.gcs_input_bucket_name
    DPU_PROCESS_BUCKET              = module.common_infra.gcs_process_bucket_name
    DPU_REJECT_BUCKET               = module.common_infra.gcs_reject_bucket_name
    DPU_REGION                      = var.region
    DPU_DATA_STORE_REGION           = var.vertex_ai_data_store_region
    DOC_PROCESSOR_JOB_NAME          = module.processor.processing_cloud_run_job_name
    DPU_DATA_STORE_ID               = google_discovery_engine_data_store.dpu_ds.data_store_id
    DOC_CLASSIFIER_JOB_NAME         = module.doc_classifier_job.classifier_cloud_run_job_name
    DOC_REGISTRY_JOB_NAME           = module.doc_registry.doc_registry_service_cloud_run_job_name
    SPECIALIZED_PARSER_JOB_NAME     = module.specialized_parser_job.specialized_parser_cloud_run_job_name
    SPECIALIZED_PROCESSORS_IDS_JSON = module.specialized_parser_job.specialized_processors_ids_json
    CUSTOM_CLASSIFIER_ID            = var.custom_classifier_id
  }
}

module "dpu_ui" {
  source                            = "../../components/webui/terraform"
  project_id                        = var.project_id
  region                            = var.region
  artifact_repo                     = module.common_infra.artifact_repo.name
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
  iap_access_domains                = var.iap_access_domains
  vertex_ai_data_store_region       = var.vertex_ai_data_store_region
  agent_builder_data_store_id       = google_discovery_engine_data_store.dpu_ds.data_store_id
  agent_builder_search_id           = google_discovery_engine_search_engine.basic.engine_id
  lb_ssl_certificate_domains        = var.webui_domains
  iap_client_id                     = module.common_infra.iap_client_id
  iap_secret                        = module.common_infra.iap_secret
  iap_member                        = module.common_infra.iap_member
  ssl_policy_link = module.common_infra.ssl_policy_link
}

module "adp_api" {
  source                            = "../../components/adp-api/terraform"
  project_id                        = var.project_id
  region                            = var.region
  artifact_repo                     = module.common_infra.artifact_repo.name
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
  iap_access_domains                = var.iap_access_domains
  lb_ssl_certificate_domains        = var.adpapi_domains
  iap_client_id                     = module.common_infra.iap_client_id
  iap_secret                        = module.common_infra.iap_secret
  iap_member                        = module.common_infra.iap_member
  ssl_policy_link = module.common_infra.ssl_policy_link
  adp_ui_url = var.adpui_domains[0]
}

module "adp_ui" {
  source                            = "../../components/adpui/terraform"
  project_id                        = var.project_id
  region                            = var.region
  artifact_repo                     = module.common_infra.artifact_repo.name
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
  iap_access_domains                = var.iap_access_domains
  lb_ssl_certificate_domains        = var.adpui_domains
  iap_client_id                     = module.common_infra.iap_client_id
  iap_secret                        = module.common_infra.iap_secret
  iap_member                        = module.common_infra.iap_member
  htil_api_endpoint                 = var.adpapi_domains[0]
  ssl_policy_link = module.common_infra.ssl_policy_link
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

    specialized_parser_cloud_run_job_name = module.specialized_parser_job.specialized_parser_cloud_run_job_name
    specialized_parser_service_account    = module.specialized_parser_job.specialized_parser_service_account

    classifier_cloud_run_job_name = local.classifier_cloud_run_job_name
    classifier_service_account    = module.doc_classifier_job.classifier_service_account

    # Agent builder
    agent_builder_location      = var.vertex_ai_data_store_region
    agent_builder_data_store_id = google_discovery_engine_data_store.dpu_ds.data_store_id
    agent_builder_search_id     = google_discovery_engine_search_engine.basic.engine_id
  })
}

module "doc_registry" {
  source                            = "../../components/doc-registry/terraform"
  project_id                        = var.project_id
  region                            = var.region
  artifact_repo                     = module.common_infra.artifact_repo.name
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
}

module "doc-deletion" {
  source                            = "../../components/doc-deletion/terraform"
  project_id                        = var.project_id
  region                            = var.region
  artifact_repo                     = module.common_infra.artifact_repo.name
  alloydb_cluster_ready             = module.common_infra.alloydb_cluster_ready
  alloy_db_cluster_id               = module.common_infra.alloydb_cluster_name
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
  serverless_connector_subnet       = module.common_infra.serverless_connector_subnet
  alloydb_primary_instance          = module.common_infra.alloydb_primary_instance
  vpc_network_name                  = module.common_infra.vpc_network_name
  data_store_project_id             = var.project_id
  data_store_region                 = var.vertex_ai_data_store_region
  data_store_id                     = google_discovery_engine_data_store.dpu_ds.data_store_id
}

module "post-setup-config" {
  source                            = "../../components/post-setup-config/terraform"
  project_id                        = var.project_id
  region                            = var.region
  artifact_repo                     = module.common_infra.artifact_repo.name
  alloydb_cluster_ready             = module.common_infra.alloydb_cluster_ready
  alloy_db_cluster_id               = module.common_infra.alloydb_cluster_name
  cloud_build_service_account_email = module.common_infra.cloud_build_service_account.email
  serverless_connector_subnet       = module.common_infra.serverless_connector_subnet
  alloydb_primary_instance          = module.common_infra.alloydb_primary_instance
  vpc_network_name                  = module.common_infra.vpc_network_name
  db_role_content_hash = sha512(join("", [
    module.specialized_parser_job.db_role_content_hash,
    module.doc-deletion.db_role_content_hash
  ]))
  additional_db_users = [
    module.specialized_parser_job.specialized_parser_db_user,
    module.doc-deletion.doc_deletion_db_user,
  ]
}
