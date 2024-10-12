provider "aws" {
  region = "eu-north-1"
}

# Import the Lambda functions module for step functions to be able to make use of the lambda functions ARN

module "lambda_functions" {
  #source = "${path.module}/lambda"  # Path to your lambda module - will give error
  source = "../lambda"
  S3_BUCKET  = var.S3_BUCKET 
} 

#module "ECR" {
  #source = "${path.module}/lambda"  # Path to your lambda module - will give error
  #source = "../../ECR"
#}
#(When you use a module, you need to provide values for all required variables defined in that module.)

# IAM policy for stfn to allow it assume policies attached to  roles it is to assume, when created. -- basic execution policy

data "aws_iam_policy_document" "stfn_execution_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["states.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}



# IAM policy to allow Step Functions to invoke the three Lambda functions created
data "aws_iam_policy_document" "stfn_invoke_lambda_policy" {
  statement {
    effect = "Allow"

    actions = ["lambda:InvokeFunction"]

    resources = [ # reference the arn output of the lambda functions
      module.lambda_functions.lambda_src_to_s3_raw_arn,
      module.lambda_functions.lambda_s3raw_to_s3staging_arn,
      "arn:aws:lambda:eu-north-1:996136076782:function:lambda_google_form_feedback",
      "arn:aws:lambda:eu-north-1:996136076782:function:lambda_customers_processing_func",
      "arn:aws:lambda:eu-north-1:996136076782:function:lambda_orders_processing_func",
      "arn:aws:lambda:eu-north-1:996136076782:function:lambda_purchase_orders_processing_func",
      "arn:aws:lambda:eu-north-1:996136076782:function:lambda_inventory_processing_func",
      "arn:aws:lambda:eu-north-1:996136076782:function:lambda_departments_processing_func",
      "arn:aws:lambda:eu-north-1:996136076782:function:lambda_suppliers_processing_func",
      "arn:aws:lambda:eu-north-1:996136076782:function:lambda_products_processing_func"
    ]
  }
}


# Create step function execution role and attach the IAM policy to the step function execution role-- Basic Execution policy attachment

resource "aws_iam_role" "stfn_execution_role" {
  name               = "stfn_execution_role"
  assume_role_policy = data.aws_iam_policy_document.stfn_execution_policy.json
}

# Attach the lambda invocation policy to the created step function execution role-- lambda invocation policy attachment

resource "aws_iam_role_policy" "stfn_invoke_lambda_policy_attachment" {
  name = "stfn_invoke_lambda_policy_attachment"
  role = aws_iam_role.stfn_execution_role.name
  policy = data.aws_iam_policy_document.stfn_invoke_lambda_policy.json
}

# Deploy the state machine

resource "aws_sfn_state_machine" "stfn_state_machine" {
  name     = "OrchestrateLambdaFunctions"
  role_arn = aws_iam_role.stfn_execution_role.arn
  definition = templatefile("${path.module}/stfn.asl.json",{
        s3_bucket        = var.S3_BUCKET
        s3_raw_prefix = "raw"
        s3_staging_prefix = "staging"
        date_suffix =  "2024-10-01"
        redshift_db_password = var.redshift_db_password
        db_password = var.db_password
  })
}



#The IAM policy you created for AWS Step Functions using the aws_iam_policy_document resource essentially allows the Step Functions service to assume an IAM role. However, the policy itself does not specify any particular actions that the Step Functions can perform; it only allows the Step Functions service (states.amazonaws.com) to assume a role.
#The action "sts:AssumeRole" allows a specified AWS service (in this case, Step Functions) to assume the IAM role that this policy is attached to.
#It means that Step Functions can "take on" the permissions associated with the IAM role.
#The principals block specifies that the principal (the entity that can perform the action) is the AWS Step Functions service (states.amazonaws.com).
#This means only the Step Functions service can use this permission to assume the role.
#Does Not Grant Specific Service Permissions: This policy only allows Step Functions to assume the IAM role. It does not define what specific actions (like invoking Lambda functions, accessing S3, etc.) the Step Functions can perform once it assumes the role.
#Does Not Directly Allow Invoking Lambda Functions: If you want Step Functions to invoke Lambda functions or access other AWS services, you would need to attach additional policies to the IAM role with specific permissions (e.g., lambda:InvokeFunction).
# we had to import the lambda functions as module so that step-functions can make use of it. e.g. when referencing the lambda functions' arn - syntax : module.lambda_functions.output_name.

#When defining an IAM policy for Step Functions to invoke Lambda, you specify the Lambda function ARNs in the resources block.
#When defining the Step Functions state machine, you provide the Lambda function ARNs as parameters in the definition file.
#You do not need to reference or worry about a separate "Lambda function invocation ARN"—it doesn’t exist in AWS terminology. 

# when you define the stfn.asl.json state machines, you will use the arn of the lambda function as well.