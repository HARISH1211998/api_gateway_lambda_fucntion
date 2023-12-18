#!/bin/bash

AWS_REGION="us-east-1"
API_GATEWAY_NAME="test-production-1"
USAGE_PLAN_NAME="xyzyx"
DYNAMODB_TABLE_NAME="test_key"

generate_uuid() {
  echo $(uuidgen)
}

get_timestamp() {
  echo $(date -u +"%Y-%m-%dT%H:%M:%SZ")
}

USAGE_PLAN_ID="zsqcia"
for ((i=1; i<100; i++)); do
  # Create API key
  API_KEY_NAME=""
  API_KEY_DESCRIPTION="Bulk Creation"

  create_key_output=$(aws apigateway create-api-key --name "$API_KEY_NAME" --description "$API_KEY_DESCRIPTION" --enabled)
  api_key_id=$(echo $create_key_output | jq -r '.id')
  api_key_value=$(echo $create_key_output | jq -r '.value')

  associate_output=$(aws apigateway create-usage-plan-key --usage-plan-id "$USAGE_PLAN_ID" --key-id "$api_key_id" --key-type "API_KEY")

  aws apigateway create-usage-plan-key --usage-plan-id xyzyx --key-type "API_KEY" --key-id $api_key_id

  uuid=$(generate_uuid)
  created=$(get_timestamp)
  updated=$created
  aws dynamodb put-item \
    --region $AWS_REGION \
    --table-name $DYNAMODB_TABLE_NAME \
    --item "{\"_id\": {\"S\": \"$uuid\"}, \"api_key_id\": {\"S\": \"$api_key_id\"}, \"created\": {\"S\": \"$created\"}, \"updated\": {\"S\": \"$updated\"}}" \
    --return-consumed-capacity TOTAL
  echo "API Key $i created with ID: $api_key_id, UUID: $uuid, Created At: $created, Updated At: $updated"
done
