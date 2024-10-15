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

module "input_bucket" {
  source                   = "github.com/terraform-google-modules/terraform-google-cloud-storage.git//modules/simple_bucket?ref=e8bb6eb49fdaf5f6f300d1b6dc46f097173dc488" # version 6.1.0, this commit is needed where kms is upgraded to 3.0, otherwise will get version conflict for google provider
  project_id               = module.project_services.project_id
  name                     = "docs-input-${var.project_id}"
  location                 = var.region
  force_destroy            = false
  labels                   = local.dpu_label
  public_access_prevention = "enforced"
}

module "process_bucket" {
  source                   = "github.com/terraform-google-modules/terraform-google-cloud-storage.git//modules/simple_bucket?ref=e8bb6eb49fdaf5f6f300d1b6dc46f097173dc488" # version 6.1.0, this commit is needed where kms is upgraded to 3.0, otherwise will get version conflict for google provider
  project_id               = module.project_services.project_id
  name                     = "dpu-process-${var.project_id}"
  location                 = var.region
  force_destroy            = false
  labels                   = local.dpu_label
  public_access_prevention = "enforced"
}

module "reject_bucket" {
  source                   = "github.com/terraform-google-modules/terraform-google-cloud-storage.git//modules/simple_bucket?ref=e8bb6eb49fdaf5f6f300d1b6dc46f097173dc488" # version 6.1.0, this commit is needed where kms is upgraded to 3.0, otherwise will get version conflict for google provider
  project_id               = module.project_services.project_id
  name                     = "dpu-reject-${var.project_id}"
  location                 = var.region
  force_destroy            = false
  labels                   = local.dpu_label
  public_access_prevention = "enforced"
}
