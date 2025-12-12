# Drata Kong Tests - Terraform Main Configuration
#
# Deploys:
# - Cloud Run Job for running tests
# - Cloud Scheduler for daily execution
# - Service account with minimal permissions

terraform {
  required_version = ">= 1.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "cloudscheduler.googleapis.com",
    "secretmanager.googleapis.com",
    "artifactregistry.googleapis.com",
  ])

  service            = each.value
  disable_on_destroy = false
}

# Service account for the job
resource "google_service_account" "job_sa" {
  account_id   = "${var.job_name}-sa"
  display_name = "Service account for Drata Kong Tests"
  description  = "Used by Cloud Run Job to run compliance tests"
}

# Grant Secret Manager access
resource "google_project_iam_member" "secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.job_sa.email}"
}

# Grant Cloud Run invoker (for scheduler)
resource "google_project_iam_member" "run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.job_sa.email}"
}

# Cloud Run Job
resource "google_cloud_run_v2_job" "tests" {
  name     = var.job_name
  location = var.region

  template {
    template {
      service_account = google_service_account.job_sa.email
      
      containers {
        image = "gcr.io/${var.project_id}/${var.job_name}:latest"

        resources {
          limits = {
            cpu    = "1"
            memory = "512Mi"
          }
        }

        # Environment variables
        env {
          name  = "KONNECT_REGION"
          value = var.konnect_region
        }

        env {
          name  = "CONTROL_PLANE_NAME"
          value = var.control_plane_name
        }

        env {
          name  = "DATAPLANE_URL"
          value = var.dataplane_url
        }

        env {
          name  = "FREE_TRIAL_KEY"
          value = var.free_trial_key
        }

        env {
          name  = "PRO_KEY"
          value = var.pro_key
        }

        env {
          name  = "GCP_PROJECT_ID"
          value = var.project_id
        }

        env {
          name  = "GCP_REGION"
          value = var.region
        }

        # Secrets from Secret Manager
        env {
          name = "KONNECT_TOKEN"
          value_source {
            secret_key_ref {
              secret  = var.konnect_token_secret
              version = "latest"
            }
          }
        }

        env {
          name = "DRATA_API_KEY"
          value_source {
            secret_key_ref {
              secret  = var.drata_api_key_secret
              version = "latest"
            }
          }
        }
      }

      timeout = "600s"  # 10 minute timeout
      
      max_retries = 1
    }
  }

  depends_on = [
    google_project_service.apis,
    google_project_iam_member.secret_accessor,
  ]
}

# Cloud Scheduler to trigger the job daily
resource "google_cloud_scheduler_job" "daily_trigger" {
  name        = "${var.job_name}-scheduler"
  description = "Triggers Drata Kong Tests daily"
  schedule    = var.schedule
  time_zone   = var.schedule_timezone
  region      = var.region

  retry_config {
    retry_count = 1
  }

  http_target {
    http_method = "POST"
    uri         = "https://${var.region}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_id}/jobs/${google_cloud_run_v2_job.tests.name}:run"

    oauth_token {
      service_account_email = google_service_account.job_sa.email
      scope                 = "https://www.googleapis.com/auth/cloud-platform"
    }
  }

  depends_on = [
    google_cloud_run_v2_job.tests,
  ]
}

