provider "aws" {
    region = "eu-north-1"
}

# Create S3 bucket
resource "aws_s3_bucket" "terraform_state" {
    bucket = "greeny-terraform-up-and-running"
}

# Configure s3 bucket versioning
resource "aws_s3_bucket_versioning" "versioning" {
    bucket = aws_s3_bucket.terraform_state.bucket

    versioning_configuration {
        status = "Enabled"
    }
}

# Create DynamoDB table for state locking
resource "aws_dynamodb_table" "terraform_lock" {
    name         = "terraform-lock-table"
    billing_mode = "PAY_PER_REQUEST"
    hash_key     = "LockID"

    attribute {
        name = "LockID"
        type = "S"
    }
}
