#!/usr/bin/env python3
from aws_cdk import core as cdk

from artificien_infrastructure.dynamo_db_stack import DynamoDBStack
from artificien_infrastructure.amplify_stack import AmplifyStack
from artificien_infrastructure.cognito_stack import CognitoStack
from artificien_infrastructure.jupyter_service_stack import JupyterServiceStack
from artificien_infrastructure.pygrid_node_stack import PygridNodeStack

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
