import boto3
import pprint
from boto3.dynamodb.conditions import Key
from aws_cdk import core
from cdk_stacks.dynamo_db_stack import DynamoDBStack


def get_sample_table_attributes():
    app = core.App()
    db = DynamoDBStack(app, "artificien-infrastructure", env={'region': 'us-east-1'})
    return db.enterprise_table_name, db.user_table_name, db.app_table_name, db.model_table_name,  db.dataset_table_name, db.region


def test_update_sample_table():
    """ Generate Sample Data for the Hello World Table"""

    # Get attributes
    enterprise_table_name, _, _, _, _, region_name = get_sample_table_attributes()

    # Test that the DynamoDB creation worked (using boto DynamoDB client):
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    
    table = dynamodb.Table(enterprise_table_name)

    # The BatchWriteItem API allows us to write multiple items to a table in one request.
    with table.batch_writer() as batch:
        batch.put_item(Item={"enterprise": "healthInsuranceGuys",
                            'num_models': 1,
                            'enterprise_account_email': "healthInsuranceGuys@hotmail.com",
                            'num_users': 2,
                            'users': None
                       })

    

def test_sample_table_queryable():
    """ Test that the DynamoDB creation worked (using boto DynamoDB client) """
    # Get attributes
    enterprise_table_name, _, _, _, _, region_name = get_sample_table_attributes()
    # Attempt GET
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    pp = pprint.PrettyPrinter(indent=2)
    
    table = dynamodb.Table(enterprise_table_name)
    response = table.get_item(Key={"enterprise": "healthInsuranceGuys"})

    if response: 
        print("\n------------SUCCESS------------\nRESPONSE:")
        pp.pprint(response)

    else:
        print("FAILED")


def populate_and_query():
    test_update_sample_table()
    test_sample_table_queryable()

if __name__ == "__main__":
    populate_and_query()
