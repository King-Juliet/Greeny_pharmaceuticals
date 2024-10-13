# GREENY_PHARMACEUTICALS

# Introduction
The aim of this project is to design and implement a robust data pipeline for Greeny Pharmaceuticals, to automate the batch extraction, transformation, and loading (ETL) of data from various sources into AWS Redshift for analytics and visualization of the key performance metrics using AWS QuickSight, to support decision making based on insight gotten from the analytics. The pipeline will also ensure data security, data governance and software engineering best practices.

# Project Requirements and Dependencies

VsCode -- The IDE used 

AWS account -- To enable one use AWS services 

Docker  -- To build locally the iamge and container to run the lambda functions

Terraform -- IaC used to provision and manage AWS resources

AWS ECR -- Repository used to hold the docker image for the lambda function to pull 

AWS Lambda function -- serverless compute used for the ETL scripts in the project.

AWS RDS  -- PostgreSQL RDS instance was used. This serves as the data source for the company. It holds raw data

Google forms -- To collect customer feedback

S3 bucket -- Serves as the comapnys datalake.

AWS Redshift -- Data warehouse for running analysis 

AWS QuickSight -- Business Intelligence tool used by the company for creating dashboards and reports 

AWS Step Functions and EventBridge : Used to orchestrate the Lambda functions for the ETL process

AWS IAM : Used to manage roles, users and permissions to resources on the company's AWS account

# How To Make Use of This Project

Link to medium article:

https://medium.com/@chibuokejuliet/building-robust-data-pipeline-for-batch-processing-with-aws-services-97356b8a8820



