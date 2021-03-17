import json
import boto3
import secrets

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table_name = 'user_table'
user_table = dynamodb.Table(table_name)


def lambda_handler(event, context):

    print(event)

    email = event["request"]["userAttributes"]["email"]
    name = event["userName"]

    api_key = secrets.token_urlsafe(16)

    user_table.put_item(
        Item={
            'user_id': email,
            'user_account_email': email,
            'username': name,
            'has_onboarded': '0',
            'role': '0',
            'api_key': api_key,
            'datasets_purchased': ['Artificien-Health']
        }
    )

    return event
