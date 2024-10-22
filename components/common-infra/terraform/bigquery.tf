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

module "docs_store_dataset" {
  source         = "github.com/terraform-google-modules/terraform-google-bigquery?ref=0fe8ab60d7291a2260cd460d55cdcca7fc815a0d" # commit hash of version 8.1.0
  dataset_id     = var.bq_store_dataset
  dataset_name   = var.bq_store_dataset
  project_id     = module.project_services.project_id
  location       = var.region
  dataset_labels = local.dpu_label
}
