terraform {
  backend "gcs" {
    bucket = "eks-int-75f65a8-eks-tf-backend"
  }
}
