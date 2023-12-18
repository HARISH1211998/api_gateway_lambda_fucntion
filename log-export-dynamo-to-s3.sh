#!/bin/bash

# Set your AWS region
AWS_REGION="us-east-1"

# Set your DynamoDB table name
DYNAMO_TABLE="test_api"

# Set your S3 bucket and folder
S3_BUCKET="s3-bucket-export"
S3_FOLDER="dynamoDB"  # Set your desired folder

# Set the current date and time for the export file
CURRENT_DATE=$(date +"%Y%m%d%H%M%S")
EXPORT_JSON_FILE="dynamodb-export-${CURRENT_DATE}.json"
EXPORT_CSV_FILE="dynamodb-export-${CURRENT_DATE}.csv"

# Export data from DynamoDB to a local JSON file
aws dynamodb scan \
    --table-name "$DYNAMO_TABLE" \
    --region "$AWS_REGION" \
    --output json \
    > "$EXPORT_JSON_FILE"

# Check if the export command was successful
if [ $? -eq 0 ]; then
    # Convert JSON to CSV using jq, extracting only the necessary attributes
    jq -r '.Items[] | {request_time_epoch: .request_time_epoch.N, created: .created.S, ip: .ip.S, extracted_url: .extracted_url.S, _id: ._id.S}' "$EXPORT_JSON_FILE" > "$EXPORT_CSV_FILE"

    # Upload the JSON file to S3
    aws s3 cp "$EXPORT_JSON_FILE" "s3://$S3_BUCKET/$S3_FOLDER/"

    # Check if the S3 upload command was successful
    if [ $? -eq 0 ]; then
        # Get the current date for cleanup
        CURRENT_DATE=$(date +"%Y%m%d%H%M%S")

        # Clean up - delete the previous export file from S3
        if [ -n "$PREVIOUS_EXPORT_KEY" ]; then
            aws s3 rm "s3://$S3_BUCKET/$S3_FOLDER/$PREVIOUS_EXPORT_KEY"
        fi

        # Clean up - delete the export files
        rm "$EXPORT_JSON_FILE"
        rm "$EXPORT_CSV_FILE"

        # Delete exported data from DynamoDB
        # Run your Python script here
        cd /home/ubuntu && python3 test.py

        # Check if the Python script completed successfully
        if [ $? -eq 0 ]; then
            echo "Python script completed successfully."
        else
            echo "Error: script failed."
        fi
    else
        echo "Error: S3 upload failed."
    fi
else
    echo "Error: DynamoDB export failed."
fi
