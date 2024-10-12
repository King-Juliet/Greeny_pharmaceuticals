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

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    #lifecycle {
      #  create_before_destroy = true
   # }
}



# Namespace
resource "aws_redshiftserverless_namespace" "greeny_data_ns" {
  namespace_name = "greeny-data-namespace"
  db_name        = "business-analytics"
  admin_username = "aduser"
  admin_user_password = var.redshift_db_password

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
