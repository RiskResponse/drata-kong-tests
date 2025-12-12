# Drata Kong Tests - Terraform Variables

variable "project_id" {
  description = "GCP project ID"
  type        = string
  default     = "drata-kong-tests"
}

variable "region" {
  description = "GCP region for Cloud Run"
  type        = string
  default     = "us-east1"
}

variable "job_name" {
  description = "Name of the Cloud Run Job"
  type        = string
  default     = "drata-kong-tests"
}

variable "schedule" {
  description = "Cron schedule for the job (UTC)"
  type        = string
  default     = "0 6 * * *"  # Daily at 6am UTC
}

variable "schedule_timezone" {
  description = "Timezone for the scheduler"
  type        = string
  default     = "UTC"
}

# Secrets - these should be stored in Secret Manager
variable "konnect_token_secret" {
  description = "Secret Manager secret name for Konnect token"
  type        = string
  default     = "konnect-token"
}

variable "drata_api_key_secret" {
  description = "Secret Manager secret name for Drata API key"
  type        = string
  default     = "drata-api-key"
}

# Kong configuration
variable "konnect_region" {
  description = "Kong Konnect region (us, eu, au)"
  type        = string
  default     = "us"
}

variable "control_plane_name" {
  description = "Kong control plane name"
  type        = string
  default     = "kong-hybrid-rate-limit-demo"
}

variable "dataplane_url" {
  description = "Kong dataplane URL"
  type        = string
}

variable "free_trial_key" {
  description = "Free trial API key"
  type        = string
  default     = "free-trial-key"
}

variable "pro_key" {
  description = "Pro tier API key"
  type        = string
  default     = "pro-key"
}

