# Drata Kong Tests - Terraform Outputs

output "job_name" {
  description = "Name of the Cloud Run Job"
  value       = google_cloud_run_v2_job.tests.name
}

output "job_uri" {
  description = "URI of the Cloud Run Job"
  value       = google_cloud_run_v2_job.tests.id
}

output "service_account_email" {
  description = "Service account email used by the job"
  value       = google_service_account.job_sa.email
}

output "scheduler_name" {
  description = "Name of the Cloud Scheduler job"
  value       = google_cloud_scheduler_job.daily_trigger.name
}

output "scheduler_schedule" {
  description = "Cron schedule for the job"
  value       = google_cloud_scheduler_job.daily_trigger.schedule
}

output "manual_trigger_command" {
  description = "Command to manually trigger the job"
  value       = "gcloud run jobs execute ${google_cloud_run_v2_job.tests.name} --region ${var.region}"
}

