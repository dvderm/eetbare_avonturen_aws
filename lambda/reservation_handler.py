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
    # Parse the incoming request body
    try:
        data = json.loads(event['body'])
        reservation_id = str(uuid.uuid4())  # Generate a unique ID for the reservation
        insertdate = str(datetime.now(ZoneInfo('Europe/Amsterdam')))
        item = {
            'id': reservation_id,
            'insertdate': insertdate,
            'name': data.get('name'),
            'email': data.get('email'),
            'date': data.get('date'),
            'time': data.get('time')
        }
        
        # Insert the item into DynamoDB
        table.put_item(Item=item)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Reservation created successfully!', 'reservation_id': reservation_id})
        }

    except Exception as e:
        print(e)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Could not create reservation'})
        }
