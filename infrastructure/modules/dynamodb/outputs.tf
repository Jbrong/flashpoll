output "polls_table" {
  value = { name = aws_dynamodb_table.polls.name, arn = aws_dynamodb_table.polls.arn }
}

output "votes_table" {
  value = { name = aws_dynamodb_table.votes.name, arn = aws_dynamodb_table.votes.arn }
}
