#!/usr/bin/env python3
from aws_cdk import core as cdk

from cdk_stacks.dynamo_db_stack import DynamoDBStack
from cdk_stacks.amplify_stack import AmplifyStack
from cdk_stacks.cognito_stack import CognitoStack
from cdk_stacks.jupyter_service_stack import JupyterServiceStack
from cdk_stacks.pygrid_node_stack import PygridNodeStack

app = cdk.App()

# Launch DynamoDB
region = 'us-east-1'
dynamo_db_stack = DynamoDBStack(app, "dynamo-db", env={'region': region})

# Launch Amplify
amplify_stack = AmplifyStack(app, 'amplify', env={'region': region})

# Launch JupyterHub
jupyter_stack = JupyterServiceStack(app, 'jupyter', env={'region': region})

# Launch Cognito to conduct authentication to the website
cognito_stack = CognitoStack(app, 'cognito', jupyter_domains=jupyter_stack.domains, env={'region': region})

# Launch Pygrid
pygrid_stack = PygridNodeStack(app, 'pygrid', env={'region': region})

app.synth()
