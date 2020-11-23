import boto3
from botocore.exceptions import ClientError
from aws_cdk import (
    core as cdk,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_efs as efs
)

import time
import logging
from efsync.utils.config.load_config import load_config
from efsync.utils.ssh.ssh_key import create_ssh_key, delete_ssh_key
from efsync.utils.ec2.ec2_main import terminate_ec2_instance
from efsync.utils.ec2.ec2_waiter import wait_for_ec2
from efsync.utils.ec2.create_user_data import create_user_data
from efsync.utils.iam_profile.iam_profile import create_iam_profile, delete_iam_profile
from efsync.utils.ec2.custom_waiter import custom_waiter


class ModelRetrievalLambda(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, iam_principals: list, **kwargs) -> None:
        """ Deploy the DynamoDB Database and Data Tables """
        super().__init__(scope, id, **kwargs)

        vpc = ec2.Vpc(self, 'ModelRetrievalLambdaVpc', max_azs=2)

        lambda_security_group = ec2.SecurityGroup(self, 'ModelRetrievalLambdaSg',
                                                  vpc=vpc, allow_all_outbound=False,
                                                  security_group_name='ModelRetrievalLambdaSg')

        efs_security_group = ec2.SecurityGroup(self, 'ModelRetrievalLambdaEfsSg',
                                               vpc=vpc, security_group_name='ModelRetrievalLambdaEfsSg')

        lambda_security_group.connections.allow_to(efs_security_group, ec2.Port.tcp(2049))  # EFS ingress
        lambda_security_group.connections.allow_to_any_ipv4(ec2.Port.all_tcp())  # explicitly allow all outbound

        # Create a file system in EFS to store python packages
        fs = efs.FileSystem(
            self,
            'ModelRetrievalLambdaFileSystem',
            vpc=vpc,
            security_group=efs_security_group,
            throughput_mode=efs.ThroughputMode.PROVISIONED,
            provisioned_throughput_per_second=cdk.Size.mebibytes(50),
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Create an access point so the lambda can access dependencies installed in EFS
        access_point_path = '/lambda'
        access_point = fs.add_access_point(
            'ModelRetrievalLambdaAccessPoint',
            create_acl=efs.Acl(owner_gid='1001', owner_uid='1001', permissions='750'),
            path=access_point_path,
            posix_user=efs.PosixUser(gid="1001", uid="1001")
        )

        # Create the lambda function
        lambda_dir = './lambdas/model_retrieval_lambda'
        self.lambda_function = _lambda.Function(
            self,
            'ModelRetrievalLambda',
            vpc=vpc,
            security_group=lambda_security_group,
            function_name='ModelRetrievalLambdaFunction',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(lambda_dir),  # directory where code is located
            handler='get_models.lambda_handler',  # the function the lambda invokes,
            memory_size=1024,  # May need a large amount of memory to download and store models temporarily
            timeout=cdk.Duration.seconds(5),
            filesystem=_lambda.FileSystem.from_efs_access_point(access_point, '/mnt/python')
        )

        # Allow the above fn to provide the lambda with required permissions for EFS/ VPC execution, then add the rest
        add_permissions_to_lambda(self.lambda_function.role)

        # Create the REST API
        self.api = apigateway.LambdaRestApi(
             self,
             'ModelRetrievalLambdaAPI',
             handler=self.lambda_function,
             policy=create_access_policy(iam_principals),
        )

        # Save the variables that we need for the post-deploy actions
        cdk.CfnOutput(self, 'efsFilesystemId', value=fs.file_system_id)
        cdk.CfnOutput(self, 'efsSecurityGroupId', value=lambda_security_group.security_group_id)
        cdk.CfnOutput(self, 'efsSubnetId', value=vpc.private_subnets[0].subnet_id)

        # This is super hacky - but for now just set this to true if you want to do the post deploy action and deploy
        # pip dependencies
        post_deploy = False

        if post_deploy:

            try:
                outputs = boto3.Session().client("cloudformation").describe_stacks(
                    StackName=self.stack_name)["Stacks"][0]["Outputs"]

                output_dict = {}
                for output in outputs:
                    key = output['OutputKey']
                    value = output['OutputValue']
                    output_dict[key] = value

            except ClientError:
                print('Not deployed yet')
                return

            except KeyError:
                print('Outputs not properly configured')
                return

            # Install pip dependencies using efsync
            config = {
                'efs_filesystem_id': output_dict['efsFilesystemId'],  # aws efs filesystem id (moint point)
                'default_sec_id': output_dict['efsSecurityGroupId'],  # security group associated with the EFS
                'security_group': output_dict['efsSecurityGroupId'],  # security group associated with the EFS
                'subnet_Id': output_dict['efsSubnetId'],  # subnet of which the efs is running in
                'ec2_key_name': 'efsync-asd913fjgq3',  # required key name for starting the ec2 instance
                'clean_efs': 'all',  # Defines if the EFS should be cleaned up before. values: `'all'`,`'pip'`,
                'aws_profile': 'default',  # aws iam profile with required permission configured in .aws/credentials
                'aws_region': self.region,  # the aws region where the efs is running
                'efs_pip_dir': access_point_path,  # pip directory on ec2
                'python_version': 3.7,
                # python version used for installing pip packages -> should be used as lambda runtime afterwards
                'requirements': lambda_dir + '/requirements.txt',
                # path + file to requirements.txt which holds the installable pip packages
            }
            logger = logging.getLogger('efsync')
            logger.setLevel(logging.DEBUG)

            start = time.time()
            logger.info('starting....')

            # load config
            logger.info('loading config')
            config = load_config(config)

            # creating ssh key for scp in memory
            logger.info('creating ssh key for scp in memory')
            try:
                config['key'] = create_ssh_key(config['bt3'],  config['ec2_key_name'])
            except Exception as e:
                raise e

            # starts ec2 instance in vpc with security group and ssh key
            logger.info(f"starting ec2 instance with security group "
                        f"{config['security_group']} and subnet_Id {config['subnet_Id']}")
            config['instance_id'] = create_ec2_instance(config)

            # stopping and deleting every resource
            # ec2
            logger.info(f"stopping ec2 instance with instance id {config['instance_id']}")
            terminate_ec2_instance(bt3=config['bt3'], instance_id=config['instance_id'])
            # iam profile
            logger.info(f"deleting iam profile")
            delete_iam_profile(config)
            # ssh key
            logger.info(f"deleting ssh key")
            delete_ssh_key(config['bt3'], config['key']['name'])

            logger.info(
                f'#################### finished after {round(time.time() - start, 2) / 60} '
                f'minutes ####################')


def add_permissions_to_lambda(lambda_role):
    lambda_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'))


def create_access_policy(iam_principals):
    # Grant each of the passed IAM principals access to use the lambda
    policy_doc = iam.PolicyDocument()
    policy_statement = iam.PolicyStatement(
        effect=iam.Effect.ALLOW,
        actions=['execute-api:Invoke'],
        resources=['execute-api:/prod/*/*/*'],  # Any REST method, on any endpoint
        principals=iam_principals
    )
    policy_doc.add_statements(policy_statement)

    return policy_doc


def create_ec2_instance(config: dict = None):
    try:
        ec2_client = config['bt3'].resource('ec2')
        instance_profile = create_iam_profile(config)
        user_data = create_user_data(config)
        # was to fast for aws after creation
        time.sleep(10)
        instance = ec2_client.create_instances(
            BlockDeviceMappings=[
                {
                    'DeviceName': '/dev/sdh',
                    'VirtualName': 'ephemeral0',
                    'Ebs': {
                        'DeleteOnTermination': True,
                        'VolumeSize': 10,
                        'VolumeType': 'gp2',
                        'Encrypted': False,
                    },
                },
            ],
            ImageId='ami-04bf6dcdc9ab498ca',
            MinCount=1,
            MaxCount=1,
            InstanceType='t2.micro',
            UserData=user_data,
            SecurityGroupIds=[
                config['security_group'],
                config['default_sec_id'],

            ],
            SubnetId=config['subnet_Id'],
            KeyName=config['key']['name'],
            IamInstanceProfile={'Arn': instance_profile['Arn']})
        # waits till it running
        wait_for_ec2(bt3=config['bt3'],
                     instance_id=instance[0].id, wait_type='start')
        # waits till user_data == 'True' tag is set
        custom_waiter(config, instance[0].id)
        return instance[0].id
    except Exception as e:
        print(repr(e))
        raise e
