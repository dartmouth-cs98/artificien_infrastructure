from aws_cdk import (
    aws_ec2 as ec2,
    core
)


class JupyterServiceStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.domains = {'callback_url': 'https://jupyter.artificien.com/hub/oauth_callback',
                        'signout_url': 'https://jupyter.artificien.com',
                        'auth_domain_name': 'artificien',
                        'auth_domain_url': 'https://artificien.auth.us-east-1.amazoncognito.com'}

        jupyter_ec2 = True
        vpc = ec2.Vpc(self,
                      "VPC",
                      subnet_configuration=[ec2.SubnetConfiguration(
                          cidr_mask=24,
                          name="Ingress",
                          subnet_type=ec2.SubnetType.PUBLIC
                      )]
                      )
        jupyter_security_group = ec2.SecurityGroup(self, "jupyter_security_group", allow_all_outbound=True, vpc=vpc)

        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80))
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv6(), ec2.Port.tcp(80))
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(443))
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv6(), ec2.Port.tcp(443))
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22))
        jupyter_security_group.add_ingress_rule(ec2.Peer.any_ipv6(), ec2.Port.tcp(22))

        if jupyter_ec2:
            # create instance
            # create userdata
            jupyter_userdata = ec2.UserData.for_linux(shebang="#!/bin/bash -xe")
            jupyter_instance = ec2.Instance(
                self,
                "jupyter_client",
                instance_type=ec2.InstanceType("t2.medium"),
                machine_image=ec2.MachineImage.generic_linux({'us-east-1': 'ami-0817d428a6fb68645'}),
                security_group=jupyter_security_group,
                vpc=vpc,
                key_name="littlest-jupyter",
                user_data=jupyter_userdata
            )
            core.Tag.add(jupyter_instance, "Name", "Little Jupyter Service")

            jupyter_userdata.add_commands(
                # install littlest jupyter hub
                "curl -L https://tljh.jupyter.org/bootstrap.py | python3 - --admin artificien",
                # Setup systemd environment variable overrides
                "mkdir /etc/systemd/system/jupyterhub.service.d",

                "echo [Service]" + "\n" + 
                "Environment=AWSCOGNITO_DOMAIN=" + str(self.domains['auth_domain_url']) + " >> /etc/systemd/system/jupyterhub.service.d/jupyterhub.conf",

                # Need to ensure oauthenticator is bumped to 0.10.0
                "curl -L https://tljh.jupyter.org/bootstrap.py | sudo python3 - --admin insightadmin",

                # Setup aws Cognito Authenticator
                "echo c.AWSCognitoAuthenticator.client_id='21lr2baklenmspuqrieju98o8s' >> /opt/tljh/config/jupyterhub_config.d/awscognito.py",
                "echo \"\" >> /opt/tljh/config/jupyterhub_config.d/awscognito.py",
                "echo c.AWSCognitoAuthenticator.client_secret='ggt3g2itnto3nedah10rpj8d424g6tfchp4kk1funmqn8jf4d92' >> /opt/tljh/config/jupyterhub_config.d/awscognito.py",
                "echo \"\" >> /opt/tljh/config/jupyterhub_config.d/awscognito.py",
                "echo c.AWSCognitoAuthenticator.oauth_callback_url='" + str(self.domains['callback_url']) + "' >> /opt/tljh/config/jupyterhub_config/awscognito.py",
                "echo \"\" >> /opt/tljh/config/jupyterhub_config.d/awscognito.py",
                "echo c.AWSCognitoAuthenticator.username_key='username' >> /opt/tljh/config/jupyterhub_config.d/awscognito.py",
                "echo \"\" >> /opt/tljh/config/jupyterhub_config.d/awscognito.py",
                "echo c.AWSCognitoAuthenticator.oauth_logout_redirect_url='" + str(self.domains['signout_url']) + "' >> /opt/tljh/config/jupyterhub_config.d/awscognito.py",

                "tljh-config set auth.type oauthenticator.awscognito.AWSCognitoAuthenticator",
                "tljh-config reload",

                # configure https to jupyter.artificien.com
                "tljh-config set https.enabled true",
                "tljh-config set https.letsencrypt.email epsteinj.us@gmail.com",
                "tljh-config add-item https.letsencrypt.domains jupyter.artificien.com",
                "tljh-config add-item https.letsencrypt.domains www.jupyter.artificien.com",
                "tljh-config reload proxy",
                # configure with preinstalled packages
                "source /opt/tljh/user/bin/activate",
                "export PATH=/opt/tljh/user/bin:${PATH}",
                "chown -R ubuntu /opt/tljh/user",
                "chmod -R +x /opt/tljh/user",
                "conda install -y python=3.7",
                "conda install -y numpy",
                "conda install -y pandas",
                "yes | pip install syft[udacity]",
            )



