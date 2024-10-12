variable "user_roles"{
    description = "Create iam user roles with these names"
    type = list(string)
    default = ["business-analyst", "business-manager", "inventory-manager", "inventory-personnel","hr", "ml-engineer"] #hyphen because of naming convention of roles
}

variable "user_names"{
    description = "Create iam user names with these names"
    type = list(string)
    default = ["Emma", "Bello", "Leo", "Gafar","Mary", "Eniola"]
}

# hr = can only add new record to the employees table on the source database 
# inventory-personnel = can only add new records to inventory table on the source database and view inventory data in s3 bucket data 
# inventory_manager = can only view inventory table in the rds and s3 bucket 
# ml engineer can access s3 bucet to get object from raw and staging data zone
# business_analyst = can access redshift and quicksight to perform analysis 
# business_manager = quicksight to view dashboard
