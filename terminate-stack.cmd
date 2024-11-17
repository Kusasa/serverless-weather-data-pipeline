REM  Deleting Lambda Functions cloudformation stack using aws-cli:
aws s3 rm s3://aw-weather-data --recursive --region us-east-1
aws cloudformation delete-stack --stack-name my-functions-stack --region us-east-1

REM Deleting my sns topic using aws-cli:
for /F "tokens=*" %%i in ('aws sns list-topics --region us-east-1 --query "Topics[?contains(TopicArn, 'weather-data-pipeline-failure')].TopicArn" --output text') do (
    set TOKEN_ARN=%%i
)
aws sns delete-topic --topic-arn %TOKEN_ARN% --region us-east-1

REM Deleting my s3 bucket using aws-cli:
aws s3 rm s3://aw-weather-functions --recursive --region us-east-1
aws s3api delete-bucket --bucket aw-weather-functions --region us-east-1

REM  Deleting AWS RDS PostgreSQL database using aws-cli:
aws rds delete-db-instance --db-instance-identifier awweatherdata --skip-final-snapshot --region us-east-1 --no-cli-pager > NUL 2>&1

REM  Deleting VPC cloudformation stack using aws-cli:
aws cloudformation delete-stack --stack-name my-vpc-stack --region us-east-1

echo "Services termination completed"