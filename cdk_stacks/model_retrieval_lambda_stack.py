from aws_cdk import (
    core as cdk,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_ec2 as ec2,
    aws_efs as efs
)


class ModelRetrievalLambda(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, iam_principals: list, **kwargs) -> None:
        """ Deploy the DynamoDB Database and Data Tables """
        super().__init__(scope, id, **kwargs)

        # Create private VPC to store lambda + EFS inside of
        vpc = ec2.Vpc(self, 'ModelRetrievalLambdaVpc', max_azs=2, nat_gateways=1)

        lambda_security_group = ec2.SecurityGroup(self, 'ModelRetrievalLambdaSg',
                                                  vpc=vpc, allow_all_outbound=False,
                                                  security_group_name='ModelRetrievalLambdaSg')

        efs_security_group = ec2.SecurityGroup(self, 'ModelRetrievalLambdaEfsSg',
                                               vpc=vpc, security_group_name='ModelRetrievalLambdaEfsSg')

        # Allow lambda to mount the EFS
        lambda_security_group.connections.allow_to(efs_security_group, ec2.Port.tcp(2049))  # EFS ingress
        lambda_security_group.connections.allow_to_any_ipv4(ec2.Port.all_tcp())  # explicitly allow all outbound

        # Create a file system in EFS to store python packages
        fs = efs.FileSystem(
            self,
            'ModelRetrievalLambdaFileSystem',
            vpc=vpc,
            security_group=efs_security_group,
            throughput_mode=efs.ThroughputMode.BURSTING, # Bursting mode adjusts throughput based on usage
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
            'ModelRetrievalLambdaFunction',
            vpc=vpc,
            security_group=lambda_security_group,
            function_name='ModelRetrievalLambdaFunction',
            runtime=_lambda.Runtime.PYTHON_3_7,
            code=_lambda.Code.from_asset(lambda_dir),  # directory where code is located
            handler='get_models.lambda_handler',  # the function the lambda invokes,
            memory_size=1024,  # May need a large amount of memory to download and store models temporarily
            timeout=cdk.Duration.seconds(60),  # may take a long time to load syft for the first time
            filesystem=_lambda.FileSystem.from_efs_access_point(access_point, '/mnt/python')
        )

        # Allow the above fn to provide the lambda with required permissions for EFS/ VPC execution, then add the rest
        add_permissions_to_lambda(self.lambda_function.role)

        # Create the REST API and allow it to invoke the lambda
        # TODO: This lambda is open to the world right now. Figure out how to use passed IAM principles to gate access.
        self.api = apigateway.LambdaRestApi(
            self,
            'ModelRetrievalLambdaAPI',
            handler=self.lambda_function,
        )

        # Create an EC2 instance to populate EFS with pip dependencies
        # This EC2 instance is deleted once done installing dependencies in EFS via the 'post_deploy_actions' script
        requirements_string = read_requirements_from_file(lambda_dir + '/requirements.txt')
        temp_userdata = ec2.UserData.for_linux(shebang="#!/bin/bash")
        temp_userdata.add_commands(
            'sudo yum update -y',
            'sudo yum install -y amazon-efs-utils',
            'sudo mkdir efs',
            'sudo mount -t efs -o tls ' + str(fs.file_system_id) + ':/ efs',
            'sudo chown -R ec2-user:ec2-user efs',
            'sudo rm -rf efs/*',
            'sudo yum install docker -y',
            'sudo service docker start',
            'sudo docker run -v "$PWD":/var/task lambci/lambda:build-python3.7 pip3 --no-cache-dir install -t efs' +
            str(access_point_path) + ' ' + str(requirements_string),
            'aws ec2 create-tags --resources $(curl http://169.254.169.254/latest/meta-data/instance-id) ' +
            '--tags \'Key=\"user_data\",Value=True\' --region ' + self.region
        )

        temp_instance = ec2.Instance(
            self, 'ModelRetrievalLambdaEc2Instance',
            instance_name='ModelRetrievalLambdaEc2Instance',
            vpc=vpc,  # same VPC as EFS and lambda
            security_group=lambda_security_group,  # Same security group as lambda so that it can access EFS
            instance_type=ec2.InstanceType('t2.micro'),
            machine_image=ec2.MachineImage.generic_linux({self.region: 'ami-04bf6dcdc9ab498ca'}),  # Amazon Linux 2
            block_devices=[ec2.BlockDevice(device_name='/dev/sdh', volume=ec2.BlockDeviceVolume.ebs(20))],
            user_data=temp_userdata
        )

        # Instance will tag itself as done (see last line of user data) once its finished installing dependencies
        # Post deploy script will check to ensure that the Ec2 instance is done before deleting it
        create_tags_permissions = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "ec2:DeleteTags",
                "ec2:CreateTags"
            ],
            resources=['*']
        )
        temp_instance.role.add_to_policy(create_tags_permissions)

        # Save the variables that we need for the post-deploy actions script
        cdk.CfnOutput(self, 'ec2InstanceId', value=temp_instance.instance_id)


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


def read_requirements_from_file(file_path):
    try:
        # read all requirements from file and remove \n
        install_list = open(file_path, 'r').read().splitlines()
        # removes empty lines and comments
        install_requires = [
            str(requirement)
            for requirement
            in install_list if not requirement.startswith('#') and len(requirement) > 0]
        return ' '.join(install_requires)

    except Exception as e:
        print(e)
        raise e
