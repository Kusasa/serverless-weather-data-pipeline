import json
import boto3
import os

def lambda_handler(event, context):
    try:
        # Extract the error message from the event
        error_message = event['error_message']
        
        # Log the error message
        print("Error message:", error_message)
        
        # Publish the error message to the SNS topic
        sns_client = boto3.client('sns')
        topic_arn = 'arn:aws:sns:us-east-1:008971661443:weather-data-pipeline-failure'
        
        response = sns_client.publish(TargetArn=topic_arn, 
                                      Message=json.dumps(event),
                                      Subject= "Failure: pipeline function experienced an issue")
        
        # Log the response from SNS
        print("SNS response:", response)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Error message sent to SNS successfully!')
        }
        
    except Exception as e:
        print("Error handling the error message:", e)
        return {
            'statusCode': 500,
            'body': json.dumps(f'Failed to send error message to SNS: {str(e)}')
        }

# Test the lambda_handler function locally
if __name__ == "__main__":
    # Sample event to test the function locally
    sample_event = {
        'error_message': 'Sample error message from Data_Fetcher'
    }
    lambda_handler(sample_event, None)