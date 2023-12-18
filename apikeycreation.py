import json
import boto3
from boto3.dynamodb.conditions import Key, Attr
from datetime import datetime
import uuid

API_GATEWAY_USAGE_PLAN = 'xyxyxy'
TABLE_NAME = 'table_name'
ATTRIBUTE_NAME = 'test_id'

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table(TABLE_NAME)
apigateway_client = boto3.client('apigateway')


def missing_required_response(message):
    return {
        'statusCode': 400,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'status': 400,
            'message': message
        })
    }
   
 
def worst_case_response(message):
    return {
        'statusCode': 500,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'status': 500,
            'message': message
        })
    }
    

def resource_not_response(message):
    return {
        'statusCode': 404,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'status': 404,
            'message': message
        })
    }


def successful_response(api_key, id):
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'status': 200,
            'installation_id': installation_id,
            'x_api_key': api_key
        })
    }


def fetch_api_key(api_key_id):
    response = apigateway_client.get_api_key(
        apiKey=api_key_id,
        includeValue=True|False
    )
    return response
    

def insert_to_dynamodb(api_key_id):
    table = dynamodb.Table(TABLE_NAME)
    try:
        # Define the data to insert
        currentDate = datetime.now().isoformat()
        item = {
            '_id': str(uuid.uuid4()),
            'installation_id': '',
            'api_key_id': api_key_id,
            'ip': '',
            'created': currentDate,
            'updated': currentDate
        }
        response = table.put_item(Item=item)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise  # Reraise the exception to propagate it
                    

def lambda_handler(event, context):
    # Check the required params!!
    if not event.get('body'):
        return missing_required_response('id is missing')
    body = json.loads(event['body'])
    if 'id' not in body:
        return missing_required_response('id is missing')
    installation_id = body.get('id')
    # Check if installation ID already exists!!
    query_expression = f"{ATTRIBUTE_NAME} = :val"
    attribute_value = installation_id
    expression_attribute_values = {':val': attribute_value}
    try:
        response = table.scan(
            FilterExpression=query_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        items = response.get('Items', [])
        if items:
            api_key_id = items[0]['id']
            try:
                response = fetch_api_key(api_key_id)
                if 'value' in response:
                    x_api_key = response['value']
                    return successful_response(x_api_key, id)
                else:
                    return missing_required_response('Unexpected response structure')
            except Exception as e:
                print(e)
                return worst_case_response('Unexpected error occur, try again')
        else:
            # installation_id does not exists
            expression_attribute_values_null = {':val': ''}
            
            try: 
                response = table.scan(
                      FilterExpression=Attr('installation_id').not_exists()
                )
                items = response['Items']
                key_details = items[0]
                key = {
                    '_id': key_details['_id']
                }
                update_expression = 'SET request_id = :request, ip = :ip, id = :id, updated = :updated '
                expression_attribute_values = {
                    ':request': event['requestContext'].get('requestId', ''),
                    ':ip': event['requestContext']['identity'].get('sourceIp', ''),
                    ':installation': installation_id,
                    ':updated': datetime.now().isoformat()
                }
                table.update_item(
                    Key=key,
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_attribute_values,
                    ReturnValues='UPDATED_NEW'
                )
                response = fetch_api_key(key_details['api_key_id'])
                if 'value' in response:
                    # Create a new key for backup!!
                    new_key = apigateway_client.create_api_key(
                        name = '',
                        description = f'',
                        enabled = True,
                        generateDistinctId = True
                    )
                    new_api_key_id = new_key['id']
                    new_api_key_value = new_key['value']
                    apigateway_client.create_usage_plan_key(
                        usagePlanId = API_GATEWAY_USAGE_PLAN,
                        keyId = new_api_key_id,
                        keyType = 'API_KEY'
                    )
                    insert_to_dynamodb(new_api_key_id)
                    
                    # Return the already activated key!!
                    x_api_key = response['value']
                    apigateway_client.update_api_key(
                        apiKey=key_details['api_key_id'],
                        patchOperations=[
                            {
                                'op': 'replace',
                                'path': '/name',
                                'value': id
                            },
                        ]
                    )
                    return successful_response(x_api_key, id)
                else:
                    return missing_required_response('Unexpected response structure')
            except Exception as e:
                print(e)
                return worst_case_response('Unexpected error occur, try again')

    except Exception as e:
        print(e)
        return worst_case_response('Unexpected error occur, try again')
