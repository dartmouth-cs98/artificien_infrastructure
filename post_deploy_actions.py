#!/usr/bin/env python3
# This script runs all post-deployment actions - actions which are not directly orchestrated by AWS or the CDK
import boto3
from godaddypy import Client, Account


def update_jupyter_dns():
    """ Updates the GoDaddy DNS Record to point to the newly launched Jupyter Service"""

    # Get the IP of the newly launched JupyterHub
    ec2 = boto3.resource('ec2')
    filters = [
        {'Name': 'tag:Name', 'Values': ['Little Jupyter Service']},
        {'Name': 'instance-state-name', 'Values': ['running']}
    ]
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])

    # There can only be one instance which exactly matches the queried name
    jupyter_instance = list(ec2.instances.filter(Filters=filters))[0]

    # Add new DNS A record to point to JupyterHub
    jupyter_ipv4 = jupyter_instance.public_ip_address
    print('Updating GoDaddy DNS Record to point to ', jupyter_ipv4)

    # Config GoDaddy
    go_daddy_api_key = 'dL3mjknFQM5d_FZGvvHrdXQCkiCbkZoB8Hg'
    go_daddy_api_secret = '59ruhpKYtfr4x81RTRXybQ'
    my_acct = Account(api_key=go_daddy_api_key, api_secret=go_daddy_api_secret)
    client = Client(my_acct)

    # Add a new A Record
    client.update_record_ip(jupyter_ipv4, 'artificien.com', 'jupyter', 'A')


# Perform all post-deployment actions
update_jupyter_dns()
