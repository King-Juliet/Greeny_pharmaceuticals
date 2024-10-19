provider "aws" {
  region = "eu-north-1"
}


#IAM ROLES AND POLICY ATTACHMENT
# CREATE POLICIES FOR ROLES

# create an assume role policy for all users
 data "aws_iam_policy_document" "iam_user_assume_role"{
    statement {
        effect = "Allow"
        principals {
        type        = "AWS"
      identifiers = [
        "arn:aws:iam::account-id:user/Emma",
        "arn:aws:iam::account-id:user/Bello",
        "arn:aws:iam::account-id:user/Leo",
        "arn:aws:iam::account-id:user/Gafar",
        "arn:aws:iam::account-id:user/Mary",
        "arn:aws:iam::account-id:user/Eniola"
        ]
    }

    actions = ["sts:AssumeRole"]
    }
 }
 
# policy to allow business analyst access redshift and also use redshift as datasource for quicksight
data "aws_iam_policy_document" "business_analyst_redshift_and_quicksight_access"{
    statement {
        effect = "Allow"
        actions = [
            "redshift:ListNamespaces",
            "redshift-serverless:GetNamespaces",
            "redshift-serverless:GetWorkgroup",
            "redshift-serverless:ListTables",
            "redshift-data:ExecuteStatement",
            "quicksight:CreateDataSource",
            "quicksight:UpdateDataSource",
        ]
        resources = [
            "arn:aws:redshift:eu-north-1:account-id:namespace:greeny-data-namespace"

        ]
    }
}


#Policy to allow business_manager interact with quicksight
data "aws_iam_policy_document" "business_manager_quicksight_access"{
    statement {
        effect = "Allow"
        actions = [
            "quicksight:RegisterUser",
            "quicksight:ListDashboards",
            "quicksight:DescribeDashboard"
        ]
        resources = ["*"]
    }
}

#Policy to allow business_analyst interact with quicksight
data "aws_iam_policy_document" "business_analyst_quicksight_access"{
    statement {
        effect = "Allow"
        actions = [
            "quicksight:RegisterUser",
            "quicksight:ListDashboards",
            "quicksight:DescribeDashboard"
        ]
        resources = ["*"]
    }
}

#policy to allow inventory manager access rds database
data "aws_iam_policy_document" "inventory_manager_rds_access"{
    statement {
        effect = "Allow"
        actions = ["rds-db:connect"]
        resources =  [
          "arn:aws:rds:eu-north-1:account-id:db:greeny_data"
]

    }
}

# policy to allow inventory personnel access rds
data "aws_iam_policy_document" "inventory_personnel_rds_access"{
    statement {
        effect = "Allow"
        actions = [
            "rds-db:connect",
            "rds-data:ExecuteStatement"
        ]
        resources = [
    "arn:aws:rds:eu-north-1:account-id:db:greeny_data"
]

    }
}

#policy to allow ml engineer access s3 bucket
data "aws_iam_policy_document" "ml_engineer_s3_access"{
    statement {
    effect = "Allow"
    actions = [
        "s3:ListBucket",
        "s3:GetObject"
    ]
    resources =[
        "arn:aws:s3:::greeny-pharma-datalake/*"
    ]
}
}

# Create IAM roles and attach policies
#Business_analyst
resource "aws_iam_role" "iam_business_analyst_user_assume_role" {
    name = "${var.user_roles[0]}-role"  #business_analyst is index 0
    assume_role_policy = data.aws_iam_policy_document.iam_user_assume_role.json
}

resource "aws_iam_role_policy" "iam_business_analyst_role" {
    role = aws_iam_role.iam_business_analyst_user_assume_role.name 
    policy = data.aws_iam_policy_document.business_analyst_redshift_and_quicksight_access.json
}

resource "aws_iam_role_policy" "business_analyst_quicksight_role_policy_attachment"{
    #count = length(var.user_roles)
    role = aws_iam_role.iam_business_analyst_user_assume_role.name

    policy = data.aws_iam_policy_document.business_analyst_quicksight_access.json
    
}

#business manager
    

resource "aws_iam_role" "iam_business_manager_assume_role" {
   name = "${var.user_roles[1]}-role" #business manager is index 1
   assume_role_policy = data.aws_iam_policy_document.iam_user_assume_role.json
}

resource "aws_iam_role_policy" "iam_business_manager_role" {
   role = aws_iam_role.iam_business_manager_assume_role.name
   policy = data.aws_iam_policy_document.business_manager_quicksight_access.json
}

#inventory manager
resource "aws_iam_role" "iam_inventory_manager_assume_role"{
  name = "${var.user_roles[2]}-role" #inventory manager is index 2
   assume_role_policy =  data.aws_iam_policy_document.iam_user_assume_role.json
}

resource "aws_iam_role_policy" "iam_inventory_manager_role" {
   role = aws_iam_role.iam_inventory_manager_assume_role.name
   policy = data.aws_iam_policy_document.inventory_manager_rds_access.json
}




#inventory personnel
resource "aws_iam_role" "iam_inventory_personnel_assume_role"{
   name = "${var.user_roles[3]}-role" #inventory personnel is index 3
   assume_role_policy = data.aws_iam_policy_document.iam_user_assume_role.json 
}

resource "aws_iam_role_policy" "iam_inventory_personnel_role" {
   role = aws_iam_role.iam_inventory_personnel_assume_role.name
   policy = data.aws_iam_policy_document.inventory_personnel_rds_access.json
}

#hr
resource "aws_iam_role" "iam_hr_assume_role"{
    name = "${var.user_roles[4]}-role" #hr is index 4
   assume_role_policy = data.aws_iam_policy_document.iam_user_assume_role.json
}

resource "aws_iam_role_policy" "iam_hr_role" {
   role = aws_iam_role.iam_hr_assume_role.name
   policy = data.aws_iam_policy_document.inventory_personnel_rds_access.json #cos they require same level of access to rds

}


#ml engineer
resource "aws_iam_role" "iam_ml_engineer_assume_role"{
   name = "${var.user_roles[5]}-role" #ml engineer is index 5
   assume_role_policy = data.aws_iam_policy_document.iam_user_assume_role.json
 
}

resource "aws_iam_role_policy" "iam_ml_engineer_role" {
   role = aws_iam_role.iam_ml_engineer_assume_role.name
   policy = data.aws_iam_policy_document.ml_engineer_s3_access.json
}

#IAM USER AND POLICY ATTACHMENT

# Create IAM users 
resource "aws_iam_user" "iam_users" {
  count         = length(var.user_names)
  name          = element(var.user_names, count.index)
  force_destroy = true
}

# Create random password for console access for each IAM user
resource "random_password" "iam_user_password" {
  count = length(var.user_names)
  length  = 16
  special = true
}

# Create login profile for console access (with a temporary password)
resource "aws_iam_user_login_profile" "iam_user_login_profiles" {
  count                = length(var.user_names)
  user                 = aws_iam_user.iam_users[count.index].name
  password             = random_password.iam_user_password[count.index].result
  password_reset_required = true  
}


# Create Access Keys for each IAM user -- for programmatic access for AWS resources
resource "aws_iam_access_key" "iam_access_keys" {
  count = length(var.user_names)
  user  = aws_iam_user.iam_users[count.index].name
}


# Store Access Keys in AWS Secrets Manager
resource "aws_secretsmanager_secret" "iam_access_keys_secret" {
  count = length(var.user_names)
  name  = "IAM_Access_Keys_${aws_iam_user.iam_users[count.index].name}"
}


# Store the Access Key ID and Secret Access Key as a secret in Secrets Manager
resource "aws_secretsmanager_secret_version" "iam_access_keys_secret_version" {
  count    = length(var.user_names)
  secret_id = aws_secretsmanager_secret.iam_access_keys_secret[count.index].id

  secret_string = jsonencode({
    access_key_id     = aws_iam_access_key.iam_access_keys[count.index].id
    secret_access_key = aws_iam_access_key.iam_access_keys[count.index].secret
  })
}


# Create policy to allow each user to access only their own secret
resource "aws_iam_policy" "iam_user_secrets_policy" {
  count = length(var.user_names)

  name        = "IAM_Secrets_Access_${aws_iam_user.iam_users[count.index].name}"
  description = "Allow IAM user to access their own secrets from Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.iam_access_keys_secret[count.index].arn
      }
    ]
  })
}

# Attach the policy to each user
resource "aws_iam_user_policy_attachment" "user_secrets_access" {
  count      = length(var.user_names)
  user       = aws_iam_user.iam_users[count.index].name
  policy_arn = aws_iam_policy.iam_user_secrets_policy[count.index].arn
}


# ALLOW USER ASSUME ROLE -- you cant directly attach roles to users, but rather allow user assume role

#Policy to allow Emma assume business analyst role
data "aws_iam_policy_document" "emma_assume_role_doc"{
   statement {
        effect = "Allow"
        actions = ["sts:AssumeRole"]
        resources = [aws_iam_role.iam_business_analyst_user_assume_role.arn]# arn for business_analyst role 
      }
   }
   
resource "aws_iam_user_policy" "emma_policy_attachment"{
    name = "emma_policy_attachment"
    #count = length(var.user_names)
    user = aws_iam_user.iam_users[0].name # emma is at index 0 on the list of roles
    policy = data.aws_iam_policy_document.emma_assume_role_doc.json

}

#Policy to allow Bello assume business manager role
data "aws_iam_policy_document" "bello_assume_role_doc"{
   statement {
        effect = "Allow"
        actions = ["sts:AssumeRole"]
        resources = [aws_iam_role.iam_business_manager_assume_role.arn] # arn for business_manager 
   }
   }

   resource "aws_iam_user_policy" "bello_policy_attachment"{
    name = "bello_policy_attachment"
    #count = length(var.user_names)
    user = aws_iam_user.iam_users[1].name # bello is at index 1 on the list of roles
    policy = data.aws_iam_policy_document.bello_assume_role_doc.json

}


#Policy to allow Leo assume inventory manager role
data "aws_iam_policy_document" "leo_assume_role_doc"{
   statement {
        effect = "Allow"
        actions = ["sts:AssumeRole"]
        resources = [aws_iam_role.iam_inventory_manager_assume_role.arn] #arn for inventory_manager 
   }
   }

resource "aws_iam_user_policy" "leo_policy_attachment"{
    name = "leo_policy_attachment"
    #count = length(var.user_names)
    user = aws_iam_user.iam_users[2].name # leo is at index 2 on the list of roles
    policy = data.aws_iam_policy_document.leo_assume_role_doc.json

}

#Policy to allow Gafar assume inventory personnel role
data "aws_iam_policy_document" "gafar_assume_role_doc"{
   statement {
        effect = "Allow"
        actions = ["sts:AssumeRole"]
        resources = [aws_iam_role.iam_inventory_personnel_assume_role.arn] # arn for inventory_personnel
   }
   }

resource "aws_iam_user_policy" "gafar_policy_attachment"{
    name = "gafar_policy_attachment"
    #count = length(var.user_names)
    user = aws_iam_user.iam_users[3].name # gafar is at index 3 on the list of roles
    policy = data.aws_iam_policy_document.gafar_assume_role_doc.json

}

#Policy to allow Mary assume hr role
data "aws_iam_policy_document" "mary_assume_role_doc"{
   statement {
        effect = "Allow"
        actions = ["sts:AssumeRole"]
        resources = [aws_iam_role.iam_hr_assume_role.arn] # arn for hr role 
   }
   }

resource "aws_iam_user_policy" "mary_policy_attachment"{
    name = "mary_policy_attachment"
    #count = length(var.user_names)
    user = aws_iam_user.iam_users[4].name # mary is at index 4 on the list of roles
    policy = data.aws_iam_policy_document.mary_assume_role_doc.json

}

#Policy to allow Eniola assume ml engineer role
data "aws_iam_policy_document" "eniola_assume_role_doc"{
   statement {
        effect = "Allow"
        actions= ["sts:AssumeRole"]
        resources = [aws_iam_role.iam_ml_engineer_assume_role.arn] # arn for ml_engineer role 
   }
   }

resource "aws_iam_user_policy" "eniola_policy_attachment"{
    name = "eniola_policy_attachment"
    #count = length(var.user_names)
    user = aws_iam_user.iam_users[5].name # eniola is at index 5 on the list of roles
    policy = data.aws_iam_policy_document.eniola_assume_role_doc.json

}












