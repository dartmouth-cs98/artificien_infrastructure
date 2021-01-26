import string
import random
from aws_cdk import (
    core as cdk,
    aws_logs as logs,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as load_balancer,
    aws_ecs_patterns as ecs_patterns,
    aws_rds as rds,
)


def create_password():
    password_characters = set(string.ascii_letters + string.digits + string.punctuation)
    password_characters -= {'/', '@', '\"'}
    password_characters = ''.join(password_characters)
    password = []
    for x in range(20):
        password.append(random.choice(password_characters))

    return ''.join(password)


class PygridNodeStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, vpc: ec2.Vpc, cluster: ecs.Cluster,  **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create the DB password
        plaintext_pw = create_password()
        password = cdk.SecretValue.plain_text(
            plaintext_pw
        )
        username = 'pygridUser'

        # Create an AWS Aurora Database
        self.db = rds.ServerlessCluster(
            self,
            'PyGridSQLCluster',
            engine=rds.DatabaseClusterEngine.AURORA_POSTGRESQL,
            parameter_group=rds.ParameterGroup.from_parameter_group_name(
                self, 'ParameterGroup', 'default.aurora-postgresql10'
            ),
            vpc=vpc,
            scaling=rds.ServerlessScalingOptions(
                auto_pause=cdk.Duration.minutes(10),
                min_capacity=rds.AuroraCapacityUnit.ACU_2,
                max_capacity=rds.AuroraCapacityUnit.ACU_8,
            ),
            default_database_name='pygridDB',
            credentials=rds.Credentials.from_password(
                username=username,
                password=password
            )
        )

        # Get the URL for the database
        db_url = 'postgresql://' + username + ':' + plaintext_pw + '@' + self.db.cluster_endpoint.hostname

        self.service = ecs_patterns.NetworkLoadBalancedFargateService(
            self, 
            'PyGridService',
            # Resources
            cluster=cluster,
            cpu=512,
            memory_limit_mib=2048,
            desired_count=1,

            # Load balancer config
            public_load_balancer=True,
            listener_port=5000,

            # Task image options
            task_image_options=ecs_patterns.NetworkLoadBalancedTaskImageOptions(
                container_name='pygrid_node',
                container_port=5000,
                image=ecs.ContainerImage.from_registry('openmined/grid-node:production'),
                environment={
                    'NODE_ID': 'node0',
                    'ADDRESS': 'http://localhost:5000',
                    'PORT': '5000',
                    'DATABASE_URL': db_url
                },
                enable_logging=True,
                log_driver=ecs.AwsLogDriver(
                    stream_prefix='PyGridNode',
                    log_group=logs.LogGroup(
                        self, 'PyGridLogGroup',
                        removal_policy=cdk.RemovalPolicy.DESTROY,
                        retention=logs.RetentionDays.ONE_MONTH
                    )
                )
            ),
            load_balancer=load_balancer.NetworkLoadBalancer(
                self, 'PyGridLoadBalancer',
                vpc=vpc,
                internet_facing=True,
                cross_zone_enabled=True
            )
        )

        # Allow ingress
        all_ports = ec2.Port(
            protocol=ec2.Protocol.TCP,
            from_port=0,
            to_port=65535,
            string_representation='All'
        )
        self.service.service.connections.allow_from_any_ipv4(all_ports)
        
        # Health Check
        self.service.target_group.configure_health_check(
            port='traffic-port',
            protocol=load_balancer.Protocol.TCP
        )
        
        # Get domain name of load balancer and output it to the console
        cdk.CfnOutput(self, 'PyGridNodeLoadBalancerDNS', value=self.service.load_balancer.load_balancer_dns_name)

        # Get access point to RDS cluster and output it to console
        cdk.CfnOutput(self, 'rdsEndpoint', value=self.db.cluster_endpoint.hostname)
