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

# Set domains for JupyterHub and Cognito
jupyter_domains = {'callback_url': 'https://jupyter.artificien.com/hub/oauth_callback',
                   'signout_url': 'https://jupyter.artificien.com',
                   'auth_domain_name': 'artificien',
                   'auth_domain_url': 'artificien.auth.' + region + '.amazoncognito.com'}

print(jupyter_domains['auth_domain_url'])

# Launch Cognito to conduct authentication to the artificien website and to JupyterHub
cognito_stack = CognitoStack(app, 'cognito', jupyter_domains=jupyter_domains, env={'region': region})

# For now we must manually get the client ID and secret from the console once Cognito is launched
jupyter_cognito_client_id = '21lr2baklenmspuqrieju98o8s'
jupyter_cognito_client_secret = 'ggt3g2itnto3nedah10rpj8d424g6tfchp4kk1funmqn8jf4d92'

# Launch JupyterHub
jupyter_stack = JupyterServiceStack(app, 'jupyter',
                                    jupyter_domains=jupyter_domains,
                                    jupyter_cognito_client_id=jupyter_cognito_client_id,
                                    jupyter_cognito_client_secret=jupyter_cognito_client_secret,
                                    instance_type='t3.medium',
                                    env={'region': region})

# Launch Pygrid
pygrid_stack = PygridNodeStack(app, 'pygrid', env={'region': region})

# Configure Dependencies:
jupyter_stack.add_dependency(cognito_stack)

app.synth()
