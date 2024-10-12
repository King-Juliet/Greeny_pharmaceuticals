provider "aws" {
  region = "eu-north-1"
}

resource "aws_ecr_repository" "lambda_repo" {
  name                 = "lambda_repo"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}

