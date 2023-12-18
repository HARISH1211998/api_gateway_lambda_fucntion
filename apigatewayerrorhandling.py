import json

def lambda_handler(event, context):
    resource_path = event['resource']
    
    def generate_response(status_code, response_message):
        return {
            'statusCode': status_code,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'status': status_code,
                'message': response_message
            })
        }
    
    if '/{proxy+}' in resource_path:
        return generate_response(404, 'The requested resource was not found')
    elif any(path in resource_path for path in ['installations', 'publishers', 'reviews', 'sources', 'verification-feedback', 'verifications', 'api-key', 'nft-metadata', 'verification-message']):
        return generate_response(405, 'The requested method was not found')
    else:
        return generate_response(404, 'The requested resource was not found')
