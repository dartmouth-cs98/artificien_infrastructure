#!/usr/bin/env python3
from aws_cdk import core as cdk

from artificien_infrastructure.dynamo_db_stack import DynamoDBStack
from artificien_infrastructure.amplify_stack import AmplifyStack
from artificien_infrastructure.cognito_stack import CognitoStack

app = cdk.App()

# Launch DynamoDB
dynamo_db_stack = DynamoDBStack(app, "dynamo-db", env={'region': 'us-east-1'})
# Launch Amplify
amplify_stack = AmplifyStack(app, 'amplify', env={'region': 'us-east-1'})
# Launch Cognito to conduct authentication to the website
cognito_stack = CognitoStack(app, 'cognito', env={'region': 'us-east-1'})

app.synth()
