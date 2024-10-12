output "lambda_src_to_s3_raw_arn" {
  value = aws_lambda_function.lambda_src_to_s3_raw.arn
}

output "lambda_s3raw_to_s3staging_arn" {
  value = aws_lambda_function.lambda_s3raw_to_s3staging.arn
}
