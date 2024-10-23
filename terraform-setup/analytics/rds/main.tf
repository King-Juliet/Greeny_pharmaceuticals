provider "aws" {
    region = "eu-north-1"
}

#Create security group for public access
resource "aws_security_group" "your_security_group" {
    name = "terraform-example4-instance"

    ingress {
        from_port   = var.server_port
        to_port     = var.server_port
        protocol    = "tcp"
        cidr_blocks = ["0.0.0.0/0"] # Consider limiting this to your IP for security
    }

    egress {
        from_port   = 0
        to_port     = 0
        protocol    = "-1"
        cidr_blocks = ["0.0.0.0/0"]
    }

    lifecycle {
        create_before_destroy = true
    }
}

# Generate admin password for postgres RDS
resource "random_password" "rds_password"{
  length = 24
  special = false
}


#Save the randomly generated admin password from line 29 to ssm
resource "aws_ssm_parameter" "rds_admin_password"{
  name = "/production/rds/admin_password"
  type = "String"
  value = random_password.rds_password.result
  tags = {
    Environment = "Production"
    Owner = "Data-engineers"
  }
}

#Retrieve existing admin username created and saved in AWS SSM parameter store
data "aws_ssm_parameter" "rds_admin_username"{
    name = "/production/rds/greeny_pharma_admin_username"
}

# Create DB instance
resource "aws_db_instance" "greeny_data" {
    engine                 = "postgres"
    allocated_storage      = 20
    max_allocated_storage  = 100 # Enable auto scaling up to 100GB max
    instance_class         = "db.t3.micro"
    storage_type           = "gp2"
    db_name                = "greeny_data"
    username               = data.aws_ssm_parameter.rds_admin_username.value
    password               = aws_ssm_parameter.rds_admin_password.value
    port                   = 5432
    publicly_accessible    = true
    backup_retention_period = 7
    multi_az               = false
    vpc_security_group_ids = [aws_security_group.your_security_group.id]
    skip_final_snapshot    = true
}
