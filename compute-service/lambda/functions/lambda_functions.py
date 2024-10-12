import json
import pandas as pd
import numpy as np
import psycopg2
from sqlalchemy import create_engine
import boto3
from datetime import datetime
from dotenv import load_dotenv
import os
import re
from io import StringIO
import pyarrow as pa
import pyarrow.parquet as pq
from io import BytesIO
from google.oauth2.service_account import Credentials
import io
import gspread
from helper_functions import check_and_replace_regex
from helper_functions import values_checker
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

#EXTRACT AND LOAD DATA FROM RDS TO S3 BUCKET
def upload_src_data_to_s3(event, context):
    db_name = event.get('db_name') 
    db_user = event.get('db_user')
    db_password = event.get('db_password')
    db_host = event.get('db_host')
    db_port = event.get('db_port') 
    schema = event.get('schema')
    tablename = event.get('tablename') 
    s3_bucket = event.get('s3_bucket') 
    s3_prefix = event.get('s3_prefix') 
    date_suffix = event.get('date_suffix')
    #uncomment this if you plan to follow the uncomment instruction
    #try: 
        ##convert user input to date formart
        #date_object = datetime.strptime(date_suffix, '%Y-%m-%d')
    #except ValueError:
        #print(f"Error encountered. Provided date, '{date_suffix}' is not in format (YYYY-mm-dd) !!")
        
            
    # Connect to PostgreSQL
    database_params = {
        "dbname": db_name,
        "user": db_user,
        "password": db_password,
        "host": db_host,
        "port": db_port
    }
    
    # Establish connection to the database
    cnxn = None
    cursor = None
    data = []
    
    try:
        cnxn = psycopg2.connect(**database_params)
        cursor = cnxn.cursor()
        # Extract data from specific product ids in the database
        sql_query = f"SELECT * FROM {schema}.{tablename} ;"

        #uncomment this to replace sql query if you want to filter record by specified date_suffix
        #sql_query = f"SELECT*FROM {schema}.{tablename} WHERE date_column = %s" #prevents sql injection cause value is user input.
        
        
        cursor.execute(sql_query)
        #uncomment this for query execution if you are uncommenting the others to replace line of code
        #cursor.execute(sql_query, (date_suffix,))

        data = cursor.fetchall()
        # Get column names
        column_names = [desc[0] for desc in cursor.description]
        # Print status message 
        print(f"Data successfully extracted from {schema}.{tablename} in {db_name} database!")
    except Exception as ex:
        print(f"Error: {ex}")
    finally:
        if cursor:
            cursor.close()
        if cnxn:
            cnxn.close()

    if not data:
        print("No data extracted. Exiting...")
        return
    
    # Write extracted data and columns to CSV
    #csv_content = ','.join(column_names) + "\n" + "\n".join([','.join(map(str, row)) for row in data])
    
    # Convert data to Pandas DataFrame
    df = pd.DataFrame(data, columns=column_names)
    # Convert DataFrame to Parquet format
    buffer = BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, buffer)
    buffer.seek(0)

    # Create boto3 client for S3 and upload data to the raw S3 bucket
    s3_client = boto3.client("s3")
    destination_filename = f"{s3_prefix}/{tablename}_{date_suffix}.parquet"
    
    try:
        s3_client.put_object(
            Body=buffer,
            #Body=csv_content,
            Bucket=s3_bucket,
            Key=destination_filename
        )
        print(f"Data successfully uploaded to S3 bucket '{s3_bucket}' with filename '{destination_filename}'")
    except Exception as ex:
        print(f"Error uploading to S3: {ex}")

#EXTRACT DATA FROM S3 RAW TO STAGING
def s3raw_to_s3staging(event, context):
    s3_bucket = event.get('s3_bucket') 
    s3_raw_prefix = event.get('s3_raw_prefix') 
    s3_staging_prefix = event.get('s3_staging_prefix')
    filename_filters = event.get('filename_filters')
    date_suffix = event.get('date_suffix')
    # Create boto3 client for S3
    s3_client = boto3.client('s3')
    
    # Extract list of objects in the raw zone of S3 bucket with specified prefix
    objects = s3_client.list_objects_v2(Bucket=s3_bucket, Prefix=s3_raw_prefix)
    
    # Print error message if content not found
    if 'Contents' not in objects:
        print("No files found in the raw prefix.")
        return
    
    for obj in objects['Contents']:
        # Extract the full filename from the S3 object key
        raw_filename = obj['Key'].split('/')[-1]
        
        # Uncomment this if you want to extract file from bucket based on specified date suffix on the file
        # if not raw_filename.endswith(date_suffix):
        #     print(f"filename '{raw_filename}' doesn't end with '{date_suffix}'. Skipping...")
        #     continue
        
        # Check if the filename matches any of the filters
        for filter_key, categories in filename_filters.items():
            if filter_key in raw_filename:
                for category in categories:
                    # Read the Parquet file from S3
                    try:
                        s3_object = s3_client.get_object(Bucket=s3_bucket, Key=obj['Key'])
                        buffer = BytesIO(s3_object['Body'].read())
                        table = pq.read_table(buffer)
                        df = table.to_pandas()

                        # Prepare the destination path
                        destination_path = f"{s3_staging_prefix}/{category}/{filter_key}_{date_suffix}.parquet"

                        # Convert DataFrame to Parquet format and upload to staging
                        buffer = BytesIO()
                        table = pa.Table.from_pandas(df)
                        pq.write_table(table, buffer)
                        buffer.seek(0)
                        
                        s3_client.put_object(
                            Body=buffer,
                            Bucket=s3_bucket,
                            Key=destination_path
                        )
                        print(f"File '{raw_filename}' successfully moved to '{destination_path}'")
                    except Exception as ex:
                        print(f"Error processing file '{raw_filename}': {ex}")
                break
        else:
            print(f"Filename '{raw_filename}' does not match any filters. Skipping...")



def google_form_to_s3(event, context):
    # Validate input parameters
    required_keys = ['sheet_url', 'sheet_name', 'bucket_name', 'credentials_key']
    if not all(key in event for key in required_keys):
        raise ValueError("Missing required parameters in event.")
    sheet_url = event.get('sheet_url') 
    sheet_name = event.get('sheet_name')
    bucket_name = event.get('bucket_name') 
    credentials_key = event.get('credentials_key')  # Key to retrieve from S3
    
    # Step 1: Prepare AWS S3 client
    s3 = boto3.client('s3')

    # Step 2: Download the credentials JSON from S3
    credentials_object = s3.get_object(Bucket=bucket_name, Key=credentials_key)
    credentials_data = credentials_object['Body'].read().decode('utf-8')  # Read and decode the JSON

    # Step 3: Setup Google Sheets API authorization
    scopes = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    credentials = Credentials.from_service_account_info(
        json.loads(credentials_data), scopes=scopes
    )

    gc = gspread.authorize(credentials)
    worksheet = gc.open_by_url(sheet_url).worksheet(sheet_name)
    
    # Step 4: Extract data from Google Sheet
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    
    # Step 5: Convert DataFrame to CSV format
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    
    # Step 6: Generate unique file name with date
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    object_key = f'feedback_data_{current_date}.csv'
    
    # Step 7: Upload the CSV to the S3 bucket
    s3.put_object(Bucket=bucket_name, Key=object_key, Body=csv_buffer.getvalue())
    print(f"Data uploaded to {bucket_name}/{object_key}")



#PROCESS CUSTOMERS DATA
def main_processing_customers(event, context):
    s3_bucket = event.get('s3_bucket')
    prefix = event.get('prefix')
    date_suffix = event.get('date_suffix')
    db_params = event.get('db_params')
    # Extract data from S3 bucket
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
    
    # Filter files by the date suffix within the specified folder
    selected_file_key = None
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(f'{date_suffix}.parquet'):  # Changed to .parquet
            selected_file_key = key
            break
    
    if not selected_file_key:
        raise FileNotFoundError(f"No file with date suffix {date_suffix} found in folder '{prefix}' of bucket {s3_bucket}.")
    
    obj = s3.get_object(Bucket=s3_bucket, Key=selected_file_key)
    data = obj['Body'].read()
    
    # Convert the data to Pandas DataFrame from Parquet format
    df = pd.read_parquet(BytesIO(data))

    # Handling customer_name column
    df['customer_name'] = df['customer_name'].str.capitalize()

    # Handling customer_gender column
    df['customer_gender'] = df['customer_gender'].str.capitalize()
    values_checker(df, 'customer_gender', ['Male', 'Female', 'Binary', 'Non-binary', 'Preferred to not say'], 'Invalid')

    # Handling customer_type column
    df['customer_type'] = df['customer_type'].str.capitalize()
    values_checker(df, 'customer_type', ['Wholesaler', 'Retailer', 'NGO'], 'Invalid')

    # Handling customer_location
    df['customer_location'] = df['customer_location'].str.upper()

    # Handle customer email
    check_and_replace_regex(df, 'customer_email', r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$', 'invalid')

    # Connect to Redshift using psycopg2
    redshift_conn = psycopg2.connect(
        dbname=db_params['dbname'],
        user=db_params['user'],
        password=db_params['password'],
        host=db_params['host'],
        port=db_params['port']
    )
    cursor = redshift_conn.cursor()

    # Insert DataFrame rows into Redshift using SQL INSERT INTO statements
    for _, row in df.iterrows():
        insert_query = f"""
        INSERT INTO {db_params['schema']}.{db_params['table_name']} (customer_id, customer_name, customer_gender, customer_birth, customer_type, customer_location, customer_email)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            row['customer_id'],
            row['customer_name'],
            row['customer_gender'], 
            row['customer_birth'],
            row['customer_type'],
            row['customer_location'],
            row['customer_email']
                ))



#PROCESS DEPARTMENTS DATA
def main_processing_departments(event, context):
    s3_bucket = event.get('s3_bucket')
    prefix = event.get('prefix')
    date_suffix = event.get('date_suffix')
    db_params = event.get('db_params')
    # Extract data from S3 bucket
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
    
    # Filter files by the date suffix within the specified folder
    selected_file_key = None
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(f'{date_suffix}.parquet'):  # Changed to .parquet
            selected_file_key = key
            break
    
    if not selected_file_key:
        raise FileNotFoundError(f"No file with date suffix {date_suffix} found in folder '{prefix}' of bucket {s3_bucket}.")
    
    obj = s3.get_object(Bucket=s3_bucket, Key=selected_file_key)
    data = obj['Body'].read()
    
    # Convert the data to Pandas DataFrame from Parquet format
    df = pd.read_parquet(BytesIO(data))

    # Handle department_name
    df['department_name'] = df['department_name'].str.capitalize() 
    values_checker(df, 'department_name', ['Inventory', 'Administration', 'Human_resource', 'Business', 'Accounts'], 'Invalid')
    
    # Handle position
    df['position'] = df['position'].str.capitalize()
    values_checker(df, 'position', ['Inventory_manager', 'Inventory_staff', 'Admin_manager', 'Admin', 'Hr_manager', 'Hr', 'Business_manager', 'Sales_rep', 'CFO', 'Accountant'], 'Invalid')

    # Connect to Redshift using psycopg2
    redshift_conn = psycopg2.connect(
        dbname=db_params['dbname'],
        user=db_params['user'],
        password=db_params['password'],
        host=db_params['host'],
        port=db_params['port']
    )
    cursor = redshift_conn.cursor()

    # Insert DataFrame rows into Redshift using SQL INSERT INTO statements
    for _, row in df.iterrows():
        insert_query = f"""
        INSERT INTO {db_params['schema']}.{db_params['table_name']} (department_id, department_name, position, salary)
        VALUES (%s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            row['department_id'],
            row['department_name'],
            row['position'], 
            row['salary'] 
                ))



#PROCESS EMPLOYEES DATA
def main_processing_employees(event, context):
    s3_bucket = event.get('s3_bucket')
    prefix = event.get('prefix')
    date_suffix = event.get('date_suffix')
    db_params = event.get('db_params')
    # Extract data from S3 bucket
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
    
    # Filter files by the date suffix within the specified folder
    selected_file_key = None
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(f'{date_suffix}.parquet'):  # Changed to .parquet
            selected_file_key = key
            break
    
    if not selected_file_key:
        raise FileNotFoundError(f"No file with date suffix {date_suffix} found in folder '{prefix}' of bucket {s3_bucket}.")
    
    obj = s3.get_object(Bucket=s3_bucket, Key=selected_file_key)
    data = obj['Body'].read()
    
    # Convert the data to Pandas DataFrame from Parquet format
    df = pd.read_parquet(BytesIO(data))

    # Handle employee_name
    df['employee_name'] = df['employee_name'].str.capitalize()

    # Handle employee_gender
    df['employee_gender'] = df['employee_gender'].str.capitalize()
    values_checker(df, 'employee_gender', ['Male', 'Female', 'Binary', 'Non-binary', 'Preferred to not say'], 'Invalid')

    # Handle employee_position
    df['employee_position'] = df['employee_position'].str.capitalize()
    values_checker(df, 'employee_position', ['Inventory_manager', 'Inventory_staff', 'Admin_manager', 'Admin', 'Hr_manager', 'Hr', 'Business_manager', 'Sales_rep', 'CFO', 'Accountant'], 'Invalid')
    
    # Handle employee_location
    df['employee_location'] = df['employee_location'].str.capitalize()

    # Handle status
    df['status'] = df['status'].str.capitalize()
    values_checker(df, 'status', ['Active', 'Not Active'], 'Invalid')

    # Connect to Redshift using psycopg2
    redshift_conn = psycopg2.connect(
        dbname=db_params['dbname'],
        user=db_params['user'],
        password=db_params['password'],
        host=db_params['host'],
        port=db_params['port']
    )
    cursor = redshift_conn.cursor()

    # Insert DataFrame rows into Redshift using SQL INSERT INTO statements
    for _, row in df.iterrows():
        insert_query = f"""
        INSERT INTO {db_params['schema']}.{db_params['table_name']} (employee_id, employee_department_id, employee_name, employee_gender, employee_birth, employee_position, employee_location, employee_email, employee_hire_date, status, resignation_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            row['employee_id'],
            row['employee_department_id'],
            row['employee_name'], 
            row['employee_gender'], 
            row['employee_birth'], 
            row['employee_position'],
            row['employee_location'],
            row['employee_email'],
            row['employee_hire_date'],
            row['status'],
            row['resignation_date']
                ))


#PROCESS INVENTORY
def main_processing_inventory(event, context):
    s3_bucket = event.get('s3_bucket')
    prefix = event.get('prefix')
    date_suffix = event.get('date_suffix')
    db_params = event.get('db_params')
    # Extract data from S3 bucket
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
    
    # Filter files by the date suffix within the specified folder
    selected_file_key = None
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(f'{date_suffix}.parquet'):  # Changed to .parquet
            selected_file_key = key
            break
    
    if not selected_file_key:
        raise FileNotFoundError(f"No file with date suffix {date_suffix} found in folder '{prefix}' of bucket {s3_bucket}.")
    
    obj = s3.get_object(Bucket=s3_bucket, Key=selected_file_key)
    data = obj['Body'].read()
    
    # Convert the data to Pandas DataFrame from Parquet format
    df = pd.read_parquet(BytesIO(data))

    # Handle product_name
    df['product_name'] = df['product_name'].str.capitalize()

    # Handle category
    df['category'] = df['category'].str.capitalize()

    # Connect to Redshift using psycopg2
    redshift_conn = psycopg2.connect(
        dbname=db_params['dbname'],
        user=db_params['user'],
        password=db_params['password'],
        host=db_params['host'],
        port=db_params['port']
    )
    cursor = redshift_conn.cursor()

    # Insert DataFrame rows into Redshift using SQL INSERT INTO statements
    for _, row in df.iterrows():
        insert_query = f"""
        INSERT INTO {db_params['schema']}.{db_params['table_name']} (product_id, product_name, category, batch, expiration_date, depot_1, depot_2, depot_3, re_order_level)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            row['product_id'],
            row['product_name'],
            row['category'], 
            row['batch'], 
            row['expiration_date'], 
            row['depot_1'],
            row['depot_2'],
            row['depot_3'],
            row['re_order_level']
                ))


#PROCESS ORDERS DATA
def main_processing_orders(event, context):
    s3_bucket = event.get('s3_bucket')
    prefix = event.get('prefix')
    date_suffix = event.get('date_suffix')
    db_params = event.get('db_params')
    # Extract data from S3 bucket
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
    
    # Filter files by the date suffix within the specified folder
    selected_file_key = None
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(f'{date_suffix}.parquet'):  # Changed to .parquet
            selected_file_key = key
            break
    
    if not selected_file_key:
        raise FileNotFoundError(f"No file with date suffix {date_suffix} found in folder '{prefix}' of bucket {s3_bucket}.")
    
    obj = s3.get_object(Bucket=s3_bucket, Key=selected_file_key)
    data = obj['Body'].read()
    
    # Convert the data to Pandas DataFrame from Parquet format
    df = pd.read_parquet(BytesIO(data))

    # Handle payment_methods
    df['payment_methods'] = df['payment_methods'].str.capitalize()
    values_checker(df=df, column_name='payment_methods', allowed_values=['Transfer', 'Cash', 'Card'], replacement_value='Invalid')

    # Connect to Redshift using psycopg2
    redshift_conn = psycopg2.connect(
        dbname=db_params['dbname'],
        user=db_params['user'],
        password=db_params['password'],
        host=db_params['host'],
        port=db_params['port']
    )
    cursor = redshift_conn.cursor()

    # Insert DataFrame rows into Redshift using SQL INSERT INTO statements
    for _, row in df.iterrows():
        insert_query = f"""
        INSERT INTO {db_params['schema']}.{db_params['table_name']} (order_date, order_id, customer_id, product_id, quantity, selling_price, employee_id, payment_methods)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            row['order_date'],
            row['order_id'],
            row['customer_id'], 
            row['product_id'], 
            row['quantity'], 
            row['selling_price'],
            row['employee_id'],
            row['payment_methods']
                ))


#PROCESS PRODUCTS DATA
def main_processing_products(event, contex):
    s3_bucket = event.get('s3_bucket')
    prefix = event.get('prefix')
    date_suffix = event.get('date_suffix')
    db_params = event.get('db_params')
    # Extract data from S3 bucket
    s3 = boto3.client('s3')
    
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
    
    # Filter files by the date suffix within the specified folder
    selected_file_key = None
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(f'{date_suffix}.parquet'):  # Changed to .parquet
            selected_file_key = key
            break
    
    if not selected_file_key:
        raise FileNotFoundError(f"No file with date suffix {date_suffix} found in folder '{prefix}' of bucket {s3_bucket}.")
    
    obj = s3.get_object(Bucket=s3_bucket, Key=selected_file_key)
    data = obj['Body'].read()
    
    # Convert the data to Pandas DataFrame from Parquet format
    df = pd.read_parquet(BytesIO(data))

    # Connect to Redshift using psycopg2
    redshift_conn = psycopg2.connect(
        dbname=db_params['dbname'],
        user=db_params['user'],
        password=db_params['password'],
        host=db_params['host'],
        port=db_params['port']
    )
    cursor = redshift_conn.cursor()

    # Insert DataFrame rows into Redshift using SQL INSERT INTO statements
    for _, row in df.iterrows():
        # Safely access 'expiring_date' using the .get() method to avoid KeyError
        expiring_date = row.get('expiring_date', None)  # Use None if 'expiring_date' is not present
        insert_query = f"""
        INSERT INTO {db_params['schema']}.{db_params['table_name']} (product_id, product_name, category, cost_price, selling_price, batch, expiring_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            row['product_id'],
            row['product_name'],
            row['category'], 
            row['cost_price'], 
            row['selling_price'], 
            row['batch'],
            expiring_date
                ))

    # Commit transaction and close connection
    redshift_conn.commit()
    cursor.close()
    redshift_conn.close()
    print(f"Data loaded into {db_params['table_name']} in {db_params['schema']} successfully.")


#PROCESS PURCHASE_ORDER DATA
def main_processing_purchase_order(event, contex):
    s3_bucket = event.get('s3_bucket')
    prefix = event.get('prefix')
    date_suffix = event.get('date_suffix')
    db_params = event.get('db_params')
    # Extract data from s3 bucket
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
    
    # Filter files by the date suffix within the specified folder
    selected_file_key = None
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(f'{date_suffix}.parquet'):  # Changed extension to .parquet
            selected_file_key = key
            break
    
    if not selected_file_key:
        raise FileNotFoundError(f"No file with date suffix {date_suffix} found in folder '{prefix}' of bucket {s3_bucket}.")
    
    obj = s3.get_object(Bucket=s3_bucket, Key=selected_file_key)
    data = obj['Body'].read()
    
    # Convert the data to Pandas DataFrame from Parquet format
    df = pd.read_parquet(BytesIO(data))

    # Handle status
    df['status'] = df['status'].str.capitalize()
    values_checker(df=df, column_name='status', allowed_values=['Delivered', 'Not delivered'], replacement_value='Invalid')
        
    # Connect to Redshift using psycopg2
    redshift_conn = psycopg2.connect(
        dbname=db_params['dbname'],
        user=db_params['user'],
        password=db_params['password'],
        host=db_params['host'],
        port=db_params['port']
    )
    cursor = redshift_conn.cursor()

    # Insert DataFrame rows into Redshift using SQL INSERT INTO statements
    for _, row in df.iterrows():
        insert_query = f"""
        INSERT INTO {db_params['schema']}.{db_params['table_name']} (purchase_order_date, purchase_order_id, supplier_id, product_id, quantity, cost_price, total_price, delivery_date, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            row['purchase_order_date'],
            row['purchase_order_id'],
            row['supplier_id'], 
            row['product_id'], 
            row['quantity'], 
            row['cost_price'],
            row['total_price'],
            row['delivery_date'],
            row['status']
        ))

    # Commit transaction and close connection
    redshift_conn.commit()
    cursor.close()
    redshift_conn.close()
    print(f"Data loaded into {db_params['table_name']} in {db_params['schema']} successfully.")


# PROCESS SUPPLIERS DATA
def main_processing_suppliers(event, context):
    s3_bucket = event.get('s3_bucket')
    prefix = event.get('prefix')
    date_suffix = event.get('date_suffix')
    db_params = event.get('db_params')
    
    # Extract data from S3 bucket
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=prefix)
    
    # Filter files by the date suffix within the specified folder
    selected_file_key = None
    for obj in response.get('Contents', []):
        key = obj['Key']
        if key.endswith(f'{date_suffix}.parquet'):
            selected_file_key = key
            break
    
    if not selected_file_key:
        raise FileNotFoundError(f"No file with date suffix {date_suffix} found in folder '{prefix}' of bucket {s3_bucket}.")
    
    # Download the Parquet file
    obj = s3.get_object(Bucket=s3_bucket, Key=selected_file_key)
    data = obj['Body'].read()

    # Convert the Parquet file data to a Pandas DataFrame
    buffer = BytesIO(data)
    table = pq.read_table(buffer)
    df = table.to_pandas()

    # Data processing
    # Handle supplier_email
    check_and_replace_regex(df=df, column_name='supplier_email', regex_pattern=r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$', replacement_value='invalid')

    # Handle supplier_location
    df['supplier_location'] = df['supplier_location'].str.upper()

    # Handle product_class
    df['product_class'] = df['product_class'].str.capitalize()
    df['product_class'] = df['product_class'].apply(lambda x: 'Raw materials' if x == 'Raw_materials' else x)
    values_checker(df=df, column_name='product_class', allowed_values=['Raw materials', 'Finished products'], replacement_value='Invalid')

    # Handle product_name
    df['product_name'] = df['product_name'].apply(
        lambda x: ', '.join(map(str, x.tolist())) if isinstance(x, np.ndarray) else str(x)
    )

    # Connect to Redshift using psycopg2
    redshift_conn = psycopg2.connect(
        dbname=db_params['dbname'],
        user=db_params['user'],
        password=db_params['password'],
        host=db_params['host'],
        port=db_params['port']
    )
    cursor = redshift_conn.cursor()

    # Insert DataFrame rows into Redshift using SQL INSERT INTO statements
    for _, row in df.iterrows():
        insert_query = f"""
        INSERT INTO {db_params['schema']}.{db_params['table_name']} (supplier_id, supplier_name, supplier_email, supplier_location, product_class, product_name)
        VALUES (%s, %s, %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (
            row['supplier_id'],
            row['supplier_name'],
            row['supplier_email'], 
            row['supplier_location'], 
            row['product_class'], 
            row['product_name']
        ))

    # Commit transaction and close connection
    redshift_conn.commit()
    cursor.close()
    redshift_conn.close()

    print(f"Data loaded into {db_params['table_name']} in {db_params['schema']} successfully.")
