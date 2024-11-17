@echo off
call myenv\Scripts\activate

@echo on
REM  Deploying VPC cloudformation stack using aws-cli:
aws cloudformation create-stack --stack-name my-vpc-stack --template-body file://IaC/vpc.yml --region us-east-1
aws cloudformation wait stack-create-complete --stack-name my-vpc-stack --region us-east-1
for /F "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name my-vpc-stack --query "Stacks[0].Outputs[?OutputKey=='SecurityGroupID'].OutputValue" --output text --region us-east-1 --no-cli-pager') do (set SECURITY_GROUP_ID=%%i)
for /F "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name my-vpc-stack --query "Stacks[0].Outputs[?OutputKey=='ServerlessWeatherPipelineSubnet01ID'].OutputValue" --output text --region us-east-1 --no-cli-pager') do (set ServerlessWeatherPipelineSubnet01ID=%%i)
for /F "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name my-vpc-stack --query "Stacks[0].Outputs[?OutputKey=='ServerlessWeatherPipelineSubnet02ID'].OutputValue" --output text --region us-east-1 --no-cli-pager') do (set ServerlessWeatherPipelineSubnet02ID=%%i)
for /F "tokens=*" %%i in ('aws cloudformation describe-stacks --stack-name my-vpc-stack --query "Stacks[0].Outputs[?OutputKey=='ServerlessWeatherPipelineSubnet03ID'].OutputValue" --output text --region us-east-1 --no-cli-pager') do (set ServerlessWeatherPipelineSubnet03ID=%%i)

REM  Creating AWS RDS PostgreSQL database using aws-cli:
aws rds create-db-instance --db-instance-identifier awweatherdata --db-instance-class db.t4g.micro --engine postgres --master-username postgres_user --master-user-password ThisIsSpartan --allocated-storage 20 --vpc-security-group-ids %SECURITY_GROUP_ID% --db-subnet-group-name serverless-weather-pipeline-db-subnet-group --db-name awweatherdata --backup-retention-period 7 --region us-east-1 --engine-version 16.3 --no-multi-az --storage-type gp2 --publicly-accessible > NUL 2>&1
aws rds wait db-instance-available --db-instance-identifier awweatherdata --region us-east-1

REM Creating my s3 bucket using aws-cli:
aws s3api create-bucket --bucket aw-weather-functions --region us-east-1

REM Uploading the dependencies of the lambda functions using aws-cli:
pip install -r .\code\requirements.txt -t .\code\dependencies_layer\python\.
7z a .\zipped\dependencies_layer.zip .\code\dependencies_layer\python
aws s3 cp .\zipped\dependencies_layer.zip s3://aw-weather-functions/

REM Uploading the lambda functions using aws-cli:
7z a .\zipped\data_fetcher.zip .\code\data_fetcher\*
7z a .\zipped\data_processor.zip .\code\data_processor\*
7z a .\zipped\error_handler.zip .\code\error_handler\*

aws s3 cp .\zipped\data_fetcher.zip s3://aw-weather-functions/
aws s3 cp .\zipped\data_processor.zip s3://aw-weather-functions/
aws s3 cp .\zipped\error_handler.zip s3://aw-weather-functions/

REM Creating my sns topic using aws-cli:
aws sns create-topic --name weather-data-pipeline-failure --region us-east-1

REM Subscribing my email addres to sns topic using aws-cli:
aws sns subscribe --topic-arn arn:aws:sns:us-east-1:008971661443:weather-data-pipeline-failure --protocol email --notification-endpoint skusasalethu@gmail.com

REM  Deploying Lambda Functions cloudformation stack using aws-cli:
aws cloudformation create-stack --stack-name my-functions-stack --template-body file://IaC/lambda_function.yml --capabilities CAPABILITY_IAM --region us-east-1 --parameters ParameterKey=ServerlessWeatherPipelineSubnet01,ParameterValue=%ServerlessWeatherPipelineSubnet01ID% ParameterKey=ServerlessWeatherPipelineSubnet02,ParameterValue=%ServerlessWeatherPipelineSubnet02ID% ParameterKey=ServerlessWeatherPipelineSubnet03,ParameterValue=%ServerlessWeatherPipelineSubnet03ID% ParameterKey=ServerlessWeatherPipelineSG,ParameterValue=%SECURITY_GROUP_ID%
aws cloudformation wait stack-create-complete --stack-name my-functions-stack  --region us-east-1

REM Specify credentials environment variables for the lambda functions using aws-cli:
aws lambda update-function-configuration --function-name data-fetcher-function --environment "Variables={AccuWeather_API_Key=%AccuWeather_API_Key%}" > NUL 2>&1
aws lambda update-function-configuration --function-name data-processor-function --environment "Variables={db_user=%db_user%,db_password=%db_password%,db_host=%db_host%,db_port=%db_port%,db_name=%db_name%}" > NUL 2>&1

echo "Deployment completed"