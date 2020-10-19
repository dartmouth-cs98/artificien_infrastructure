#!/usr/bin/env python3
from aws_cdk import core
from artificien_infrastructure.dynamo_db_stack import DynamoDBStack

# Launch DynamoDB
app = core.App()
DynamoDBStack(app, "dynamo-db", env={'region': 'us-east-1'})
app.synth()
