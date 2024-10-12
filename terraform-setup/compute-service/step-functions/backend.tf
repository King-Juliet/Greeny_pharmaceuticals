terraform {
  backend "s3" {
    bucket         = "greeny-terraform-up-and-running"
    key            = "stepfunctions/terraform.tfstate" 
    region         = "eu-north-1"
    dynamodb_table = "terraform-lock-table" # For state locking
    encrypt        = true
  }
}
