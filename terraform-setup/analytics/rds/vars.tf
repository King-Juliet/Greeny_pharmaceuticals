variable "db_password" {
  description = "Password for the PostgreSQL database"
  type        = string
  sensitive   = true
  default = "yourpassword"
}

variable "server_port"{
    description = "The port the server will use for HTTP request"
    default = 5432
}