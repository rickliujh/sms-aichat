locals {
  tags = {
    app = "sms-aichat"
    env = "dev"
  }
}

module "aws-tf-backend" {
  source = "./modules/init-backend"

  state_file_aws_region          = "us-east-1"
  state_file_bucket_name         = "tf-state-sms-aichat"
  override_state_lock_table_name = "tf-state-lock-sms-aichat"
  override_aws_tags              = local.tags
}

