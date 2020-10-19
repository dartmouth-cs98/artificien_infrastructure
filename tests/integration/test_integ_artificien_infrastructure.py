import boto3
from boto3.dynamodb.conditions import Key
from aws_cdk import core
from artificien_infrastructure.dynamo_db_stack import DynamoDBStack


def get_sample_table_attributes():
    app = core.App()
    db = DynamoDBStack(app, "artificien-infrastructure", env={'region': 'us-east-1'})
    return db.sample_table_name, db.region


def test_update_sample_table():
    """ Generate Sample Data for the Hello World Table"""

    # Get attributes
    sample_table_name, region_name = get_sample_table_attributes()

    # Test that the DynamoDB creation worked (using boto DynamoDB client):
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(sample_table_name)

    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with table.batch_writer() as batch:
        batch.put_item(Item={"user_id": "kenneym", "Name": "Matt Kenney",
                             "Skills": {"Swag": 100, "Genius": "Yes"}})
        batch.put_item(Item={"user_id": "shreyas-v-agnihotri", "Name": "Shreyas Agnihotri",
                             "Skills": {"Swag": 100, "Genius": "Yes"}})
        batch.put_item(Item={"user_id": "tobiaslange18", "Name": "Tobias Lange",
                             "Skills": {"Swag": 100, "Genius": "Yes"}})
        batch.put_item(Item={"user_id": "AlexQuill", "Name": "Alex Quill",
                             "Skills": {"Swag": 100, "Genius": "Yes"}})
        batch.put_item(Item={"user_id": "epsteinj", "Name": "Jake Epstein",
                             "Skills": {"Swag": 100, "Genius": "Yes"}})


def test_sample_table_queryable():
    """ Test that the DynamoDB creation worked (using boto DynamoDB client) """
    # Get attributes
    sample_table_name, region_name = get_sample_table_attributes()

    # Attempt GET
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(sample_table_name)
    response = table.get_item(Key={"user_id": "AlexQuill"})
    print(response['Item'])
