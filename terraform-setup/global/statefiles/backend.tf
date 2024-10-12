terraform {
  backend "s3" {
    bucket         = "greeny-terraform-up-and-running" 
    key            = "global/state-files/terraform.tfstate"
    region         = "eu-north-1"
    dynamodb_table = "terraform-lock-table" # For state locking
    encrypt        = true
  }
}

#once statefiles bucket is created, then you can uncomment this and run terraform init again