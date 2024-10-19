provider "aws" {
  region = "eu-north-1"
}


#Create security group for public access
resource "aws_security_group" "redshift_security_group" {
    name = "redshift-security-group"

    ingress {
        from_port   = 5439 #port number of the postgres
        to_port     = 5439 #port number of the postgres
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"] # Consider limiting this to your IP for security
    }

     
}

# Generate admin password for redshift
resource "random_password" "redshift_password"{
  length = 24
  special = false
}


#Save the randomly generated admin password from line 29 to ssm
resource "aws_ssm_parameter" "redshift_admin_password"{
  name = "/redshift/admin_password"
  type = "String"
  value = random_password.redshift_password.result
}

# Namespace
resource "aws_redshiftserverless_namespace" "greeny_data_ns" {
  namespace_name = "greeny-data-namespace"
  db_name        = "business-analytics"
  admin_username = "aduser"
  admin_user_password = aws_ssm_parameter.redshift_admin_password.value

  tags = {
    Name = "greeny-data-namespace"
  }
}

# Workgroup
resource "aws_redshiftserverless_workgroup" "greeny_data_wg" {
  workgroup_name     = "greeny-data-workgroup"
  namespace_name     = aws_redshiftserverless_namespace.greeny_data_ns.namespace_name
  base_capacity      = 8
  publicly_accessible = true
  security_group_ids = [aws_security_group.redshift_security_group.id]

  tags = {
    Name = "pharma-data-workgroup"
  }
}
