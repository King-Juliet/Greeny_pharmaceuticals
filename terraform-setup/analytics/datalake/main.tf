provider "aws" {
    region = "eu-north-1"
}

# Create S3 bucket
resource "aws_s3_bucket" "data_lake" {
    bucket = "greeny-pharma-datalake"
}
