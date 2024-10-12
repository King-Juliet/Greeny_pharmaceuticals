output "stfn_state_machine_arn" {
  value = aws_sfn_state_machine.stfn_state_machine.arn
}

#value = resourcename.nameid.arn  (resourcename and nameid gotten from the reource block of interest. )