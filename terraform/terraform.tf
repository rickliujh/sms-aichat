# Generated by the module.
terraform {
  backend "s3" {
    bucket         = "tf-state-sms-aichat"
    key            = "terraform-state"
    region         = "us-east-1"
    encrypt        = true
    kms_key_id     = "alias/aws/s3"
    dynamodb_table = "tf-state-lock-sms-aichat"
  }
}
