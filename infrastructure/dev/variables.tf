variable "project_name" {
  type        = string
  description = "The name of the project."
}

variable "environment" {
  type        = string
  description = "The environment in which the application is running (e.g., dev, test, prod)."
}

variable "ses_from_email" {
  type        = string
  description = "The email address to be used as the 'From' address in SES emails."
}


