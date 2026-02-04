resource "aws_iam_role" "calendar" {
  name = "calendar-dev"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_policy" "calendar" {
  name = "calendar-dev"
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "ssm:GetParameter",
          "ssm:PutParameter"
        ],
        Resource = [
          "arn:aws:ssm:*:${data.aws_caller_identity.current.account_id}:parameter/calendar/dev/*",
          "arn:aws:ssm:*:${data.aws_caller_identity.current.account_id}:parameter/ops-master/cloudfront/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = "arn:aws:dynamodb:*:${data.aws_caller_identity.current.account_id}:table/calendar-events-dev"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "calendar" {
  role       = aws_iam_role.calendar.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy_attachment" "calendar_api_policy" {
  role       = aws_iam_role.calendar.name
  policy_arn = aws_iam_policy.calendar.arn
}
