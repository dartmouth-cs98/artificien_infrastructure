from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    core as cdk
)


class JupyterServiceStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct,
                 id: str,
                 jupyter_domains: dict,
                 jupyter_cognito_client_id: str,
                 jupyter_cognito_client_secret: str,
                 instance_type: str,
                 **kwargs) -> None:

        super().__init__(scope, id, **kwargs)

        jupyter_ec2 = True
        vpc = ec2.Vpc(
            self,
            "VPC",
            subnet_configuration=[ec2.SubnetConfiguration(
                    cidr_mask=24,
                    name="Ingress",
                    subnet_type=ec2.SubnetType.PUBLIC
            )]
        )

        # Configure Security Group
        jupyter_security_group = ec2.SecurityGroup(self, "jupyter_security_group", allow_all_outbound=True, vpc=vpc)
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))  # HTTP
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv6(), ec2.Port.tcp(80))
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443))  # HTTPS
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv6(), ec2.Port.tcp(443))
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22))  # SSH (For Troubleshooting)
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv6(), ec2.Port.tcp(22))

        self.jupyter_instance = None

        if jupyter_ec2:

            # create userdata
            letsencrypt_email = 'epsteinj.us@gmail.com'
            letsencrypt_domain = 'jupyter.artificien.com'
            github_auth_token = '084f381f25c76d5b417ccfae922a36215bc87950'

            jupyter_userdata = ec2.UserData.for_linux(shebang="#!/bin/bash -x")
            jupyter_userdata.add_commands(
                ##############################
                # install littlest jupyter hub
                ##############################
                "curl -L https://tljh.jupyter.org/bootstrap.py | python3 - --admin artificien",

                ##############################################
                # Setup systemd environment variable overrides
                ##############################################
                "mkdir /etc/systemd/system/jupyterhub.service.d",

                "echo \"[Service]",
                "Environment=AWSCOGNITO_DOMAIN=" + jupyter_domains['auth_domain_url'] + \
                "\" >> /etc/systemd/system/jupyterhub.service.d/jupyterhub.conf",

                #################################
                # Setup aws Cognito Authenticator
                #################################
                # Need Single quotes around all variables since we are passing this into a python script
                "echo \"c.AWSCognitoAuthenticator.client_id=\'" + jupyter_cognito_client_id + "\'",
                "c.AWSCognitoAuthenticator.client_secret=\'" + jupyter_cognito_client_secret + "\'",
                "c.AWSCognitoAuthenticator.oauth_callback_url=\'" + jupyter_domains['callback_url'] + "\'",
                "c.AWSCognitoAuthenticator.username_key=\'username\'",
                "c.AWSCognitoAuthenticator.oauth_logout_redirect_url=\'" + jupyter_domains['signout_url'] + "\'" + \
                "\" >> /opt/tljh/config/jupyterhub_config.d/awscognito.py",

                ###################################################
                # Need to ensure oauthenticator is bumped to 0.10.0
                ###################################################
                "curl -L https://tljh.jupyter.org/bootstrap.py | sudo python3 - --admin insightadmin",

                # Reload Config
                "tljh-config set auth.type oauthenticator.awscognito.AWSCognitoAuthenticator",
                "tljh-config reload",

                ###########################################
                # Configure HTTPS to jupyter.artificien.com
                ###########################################
                "tljh-config set https.enabled true",
                "tljh-config set https.letsencrypt.email " + letsencrypt_email,
                "tljh-config add-item https.letsencrypt.domains " + letsencrypt_domain,
                "tljh-config add-item https.letsencrypt.domains www." + letsencrypt_domain,
                "tljh-config reload proxy",

                ######################################
                # configure with preinstalled packages
                ######################################
                "sudo apt install aws-cli"
                "source /opt/tljh/user/bin/activate",
                "export PATH=/opt/tljh/user/bin:${PATH}",
                "chown -R ubuntu /opt/tljh/user",
                "chmod -R +x /opt/tljh/user",
                "conda install -y python=3.8",
                "conda install -y numpy",
                "conda install -y pandas",

                ###################
                # Enable Jupyterlab
                ###################
                "sudo tljh-config set user_environment.default_app jupyterlab",
                "sudo tljh-config reload hub",
                
                ##############################
                # Install Artificien library #
                ##############################
                "git clone https://" + github_auth_token + "@github.com/dartmouth-cs98/artificien_experimental.git",
                "pip install -e ./artificien_experimental/artificienLibrary",

                ###############################
                # Get Fake Data and Tutorials #
                ###############################
                "sudo mkdir -p /srv/data/sample_data",
                "sudo mkdir /srv/data/tutorials",

                # Get the tutorial notebook(s)
                "cd /srv/data/tutorials",
                "sudo git clone https://" + github_auth_token + "@github.com/dartmouth-cs98/artificien_tutorials.git .",

                # Get the sample data
                "cd /srv/data/sample_data",
                "aws s3 cp s3://artificien-fake-dataset-storage//tmp/ . --recursive",

                # Create symbolic link
                "cd /etc/skel",
                "sudo ln -s /srv/data/sample_data sample_data"
            )

            # create instance
            self.jupyter_instance = ec2.Instance(
                self,
                "jupyter_client",
                instance_type=ec2.InstanceType(instance_type),
                machine_image=ec2.MachineImage.generic_linux({self.region: 'ami-0817d428a6fb68645'}),  # Ubuntu AMI
                block_devices=[ec2.BlockDevice(device_name='/dev/sda1', volume=ec2.BlockDeviceVolume.ebs(50))],  # 50 GB
                security_group=jupyter_security_group,
                vpc=vpc,
                key_name="littlest-jupyter",  # Use the Key in this repo to SSH into the machine
                user_data=jupyter_userdata
            )

            # Give the instance role access to S3 (to get sample data) and Dynamo (to store user models)
            self.jupyter_instance.role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'))
            self.jupyter_instance.role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'))

            # Give instance a name
            cdk.Tags.of(self.jupyter_instance).add('Name', 'Little Jupyter Service')

            cdk.CfnOutput(self, 'JupyterIPv4', value=self.jupyter_instance.instance_public_ip)
