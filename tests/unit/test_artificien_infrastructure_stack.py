import json
from aws_cdk import core
from cdk_stacks.dynamo_db_stack import DynamoDBStack


def get_template():
    app = core.App()
    DynamoDBStack(app, "artificien-infrastructure", env={'region': 'us-east-1'})
    return json.dumps(app.synth().get_stack("artificien-infrastructure").template)


def test_dynamo_table_created():
    assert("AWS::DynamoDB::Table" in get_template())


def test_front_end_role_created():
    assert("AWS::IAM::Policy" in get_template())
    assert("dynamodb:BatchGetItem" in get_template())  # check that permissions are showing up
