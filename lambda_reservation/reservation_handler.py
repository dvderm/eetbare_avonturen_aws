import os
import json
import uuid
import boto3
from datetime import datetime
from zoneinfo import ZoneInfo

# Picking up relevant environment variables from the reservation_lambda and storing them in variables to be used in this script (script of the handler)
# For DynamoDB
dynamodb = boto3.resource('dynamodb')
table_name = os.environ['TABLE_NAME']
table = dynamodb.Table(table_name)
# For SES
ses = boto3.client('ses')
sender_email = os.environ['SENDER_EMAIL']


def lambda_handler(event, context):

    # Log incoming JSON data that goes from frontend to backend
    print(f'Logging: {json.dumps(event)}')

    # Load data from incoming JSON into DynamoDB table
    try:
        data = json.loads(event['body'])
        reservation_id = str(uuid.uuid4())
        insertdate = str(datetime.now(ZoneInfo('Europe/Amsterdam')))
        item = {
            'id': reservation_id,
            'insertdate': insertdate,
            'email': data.get('email'),
            'date': data.get('date'),
            'time': data.get('time')
        }
        
        # Log incoming insert into DynamoDB table
        print(f'Logging: inserting following data into DynamoDB: {item}')

        # Insert the item into DynamoDB
        table.put_item(Item=item)

        # Send confirmation email
        send_confirmation_email(ses, item)

        success_response = {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',  # Replace '*' with your domain for more secure access
                'Access-Control-Allow-Methods': 'POST',
                'Access-Control-Allow-Headers': 'Content-Type'
            },
            'body': json.dumps({'message': 'Reservation created successfully!', 'reservation_id': reservation_id})
        }

        print(f'Logging: succes response from backend to frontend: {json.dumps(success_response)}')

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

def send_confirmation_email(ses, reservation):

    # Adding logging
    print(f"""Logging: mailadres klant: {reservation['email']}""")

    subject = "Reserveringsbevestiging"
    body = f"""
    Beste, 

    Hartelijk dank voor de bestelling met bestelcode {reservation['id']} op {reservation['date']} om {reservation['time']}! 

    Hieronder nogmaals een overzicht: 

    Bestelcode: {reservation['id']}
    Datum: {reservation['date']}
    Aanvangstijd: {reservation['time']}

    Met vriendelijke groet,

    Eetbare Avonturen
    """

    try:
        ses.send_email(
            Source=sender_email,
            Destination={
                'ToAddresses': [reservation['email']]
            },
            Message={
                'Subject': {'Data': subject},
                'Body': {'Text': {'Data': body}}
            }
        )
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        print(f"Full error details: {json.dumps(e.__dict__, default=str)}")