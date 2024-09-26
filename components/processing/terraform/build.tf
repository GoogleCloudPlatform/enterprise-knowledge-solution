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
  registry_url = "${var.repository_region}-docker.pkg.dev/${var.project_id}/${var.artifact_repo}"
  cloud_build_fileset = [
    "${path.module}/build/cloudbuild.yaml.template",
    "${path.module}/build/cloudbuild.yaml",
    "${path.module}/build/Dockerfile",
    "${path.module}/build/requirements.txt",
  ]
  lib_source_directory_path = "${path.module}/../libs"
  lib_source_fileset        = [for f in fileset(local.lib_source_directory_path, "**/*.py") : "${local.lib_source_directory_path}/${f}"]
  all_dependent_fileset     = setunion(local.cloud_build_fileset, local.lib_source_fileset)
  cloud_build_content_hash  = sha512(join("", [for f in local.all_dependent_fileset : fileexists(f) ? filesha512(f) : sha512("file-not-found")]))
}

# Depends on: input bucket, artefactory (registury_url), and docprocessor service account
resource "local_file" "cloudbuild_cloud_run" {
  filename = "${path.module}/build/cloudbuild.yaml"
  content = templatefile("${path.module}/build/cloudbuild.yaml.template", {
    project_id                    = var.project_id,
    registry_url                  = local.registry_url,
    region                        = var.region,
    service_account               = module.doc_processor_account.email
    processing_cloud_run_job_name = var.processing_cloud_run_job_name
    build_service_account         = var.cloud_build_service_account_email
  })
}

# See github.com/terraform-google-modules/terraform-google-gcloud
module "gcloud" {
  source = "github.com/terraform-google-modules/terraform-google-gcloud?ref=db25ab9c0e9f2034e45b0034f8edb473dde3e4ff" # commit hash of version 3.5.0

  create_cmd_entrypoint = "gcloud"
  create_cmd_body       = <<-EOT
    builds submit \
      --project ${var.project_id} \
      --region ${var.region} \
      --config ${local_file.cloudbuild_cloud_run.filename} \
      "${path.module}/../../.."
  EOT
  enabled               = true

  create_cmd_triggers = {
    source_contents_hash = local.cloud_build_content_hash
  }
}
