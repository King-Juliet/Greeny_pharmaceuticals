# Use Python 3.8 AWS Lambda runtime as the base image
FROM public.ecr.aws/lambda/python:3.8

# Set the working directory in the container
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy the Python script into the Lambda task root directory
COPY functions/lambda_functions.py ${LAMBDA_TASK_ROOT}

# Copy the helper Python script into the Lambda task root directory
COPY functions/helper_functions.py ${LAMBDA_TASK_ROOT}

# Copy the requirements file and install dependencies
COPY functions/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Specify the handler function to be invoked by Lambda
#CMD [ "lambda_functions.upload_src_data_to_s3" ]


