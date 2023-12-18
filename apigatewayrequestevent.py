import json
import boto3
from datetime import datetime


def lambda_handler(event, context):
    # Initialize the DynamoDB resource
    dynamodb = boto3.resource('dynamodb')
    
    # Define your DynamoDB table name
    table_name = 'example_traffic_event'
    
    # Get a reference to the DynamoDB table
    table = dynamodb.Table(table_name)
    permission = "Allow"
    
    try:
        # Define the data to insert
        item = {
            '_id': event['requestContext'].get('requestId', ''),
            'installation_id': event['queryStringParameters'].get('installation_id', ''),
            'unique_id': event['queryStringParameters'].get('unique_id', ''),
            'example_url': event['queryStringParameters'].get('example_url', ''),
            'ip': event['requestContext']['identity'].get('sourceIp', ''),
            'request_time_epoch': event['requestContext'].get('requestTimeEpoch', ''),
            'created': datetime.now().isoformat(),
            'updated': datetime.now().isoformat()
        }
        
        response = table.put_item(Item=item)
    
    except Exception as e:
        # Handle exceptions or errors here
        print(f"An error occurred: {str(e)}")
        permission = "Deny"
    
    finally:
        print("_id: " + event['queryStringParameters'].get('_id', ''))
        # Always return a policy that allows access
        policy = {
            "principalId": "user",
            "policyDocument": {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Action": "execute-api:Invoke",
                        "Effect": permission,
                        "Resource": "*"
                    }
                ]
            }
        }
        return policy
