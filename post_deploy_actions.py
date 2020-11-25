#!/usr/bin/env python3
# This script runs all post-deployment actions - actions which are not directly orchestrated by AWS or the CDK
import boto3
from botocore.exceptions import ClientError
from godaddypy import Client, Account


def get_outputs(stack_name: str):
    """ Helper function to get CfnOutputs from deployed stacks"""
    try:
        outputs = boto3.Session().client("cloudformation").describe_stacks(
            StackName=stack_name)["Stacks"][0]["Outputs"]

        output_dict = {}
        for output in outputs:
            key = output['OutputKey']
            value = output['OutputValue']
            output_dict[key] = value

        return output_dict

    except ClientError:
        print('Cloudformation Stack might not be deployed yet')
        return

    except KeyError:
        print('Cloudformation Outputs for the', stack_name, 'stack are not properly configured')
        return


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


def delete_temporary_ec2():
    """
    Deletes the ec2 instance that was temporarily created
    in order to install large pip dependencies into the lambda
    """
    # Get EC2 Instance ID
    output_dict = get_outputs(stack_name='modelRetreivalLambda')
    if output_dict is None:
        return
    instance_id = output_dict['ec2InstanceId']

    # Delete instance, if it is done loading dependencies into EFS
    session = boto3.session.Session()
    ec2_resource = session.resource('ec2')
    ec2instance = ec2_resource.Instance(instance_id)
    if ec2instance.tags is not None:
        # checks if user_data tag is true
        done = False
        for tags in ec2instance.tags:
            if tags['Key'] == 'user_data' and tags['Value'] == 'True':
                done = True
                ec2instance.terminate()
                print('Terminated Instance')

        if not done:
            print('Instance not yet done installing pip dependencies')
    else:
        print('Instance is not yet started')


# Perform all post-deployment actions
# update_jupyter_dns()
delete_temporary_ec2()
