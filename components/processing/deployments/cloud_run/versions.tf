terraform {
  required_version = ">=1.5.7"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.23.0"
    }
    time = {
      source  = "hashicorp/time"
      version = "0.12.1"
    }
    local = {
      source  = "hashicorp/local"
      version = "2.5.2"
    }
  }

  provider_meta "google" {
    module_name = "cloud-solutions/dpu-solution-v1.0.0"
  }
}
