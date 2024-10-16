variable "create_vpc_network" {
  type = bool
  description = ""
  default = true
}

variable "vpc_name" {
  type = string
  description = "eks-vpc"
  default = "eks-vpc"
}

variable "project_id" {
  type = string
  description = "project id"
  default = "eks1-2-1"
}