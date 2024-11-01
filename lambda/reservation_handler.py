import os
import json
import uuid
import boto3
from datetime import datetime
from zoneinfo import ZoneInfo

dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)

def lambda_handler(event, context):

    # Log incoming JSON data that goes from frontend to backend
    print(json.dumps(event))

    # Load data from incoming JSON into DynamoDB table
    try:
        data = json.loads(event['body'])
        reservation_id = str(uuid.uuid4())
        insertdate = str(datetime.now(ZoneInfo('Europe/Amsterdam')))
        item = {
            'id': reservation_id,
            'insertdate': insertdate,
            'email': data.get('name'),
            'date': data.get('date'),
            'time': data.get('time')
        }
        
        print(f'Inserting following data into DynamoDB: {item}')

        # Insert the item into DynamoDB
        table.put_item(Item=item)

        success_response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',  # Replace '*' with your domain for more secure access
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'message': 'Reservation created successfully!', 'reservation_id': reservation_id})
        }

        print(f'Succes response from backend to frontend: {json.dumps(success_response)}')

        return success_response

    except Exception as e:
        print(f'Error response: {e}')

        return {
            'statusCode': 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'error': 'Could not create reservation'})
        }
