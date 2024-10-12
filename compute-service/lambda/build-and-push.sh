#!/bin/bash

# Variables (Replace these with your actual values)
REPO_NAME="lambda_repo"
AWS_ACCOUNT_ID="account-id"
REGION="eu-north-1"
IMAGE_TAG="latest"

# Build Docker image
docker build -t my-lambda-function .

# Tag Docker image
docker tag my-lambda-function:latest $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com
# Push Docker image to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG
