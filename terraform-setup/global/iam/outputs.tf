output "users_arn"{
    description = "arn for all the created iam users"
    value = ["${aws_iam_user.iam_users.*.arn}"]
}

