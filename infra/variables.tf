variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "eu-west-1"
}

variable "project_name" {
  description = "Prefix used in resource names and tags"
  type        = string
  default     = "ms-fargate"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "az_count" {
  description = "Number of Availability Zones to span"
  type        = number
  default     = 2
}

variable "single_nat_gateway" {
  description = "true = one shared NAT Gateway (cheaper, demo). false = one per AZ (highly available, production)."
  type        = bool
  default     = true
}
