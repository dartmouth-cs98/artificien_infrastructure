from aws_cdk import (
    core as cdk,
    aws_iam as iam,
    aws_logs as logs,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_elasticloadbalancingv2 as load_balancer,
    aws_ecs_patterns as ecs_patterns,
)


class OrchestrationStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, vpc: ec2.Vpc, cluster: ecs.Cluster, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        lb = load_balancer.NetworkLoadBalancer(
            self, 'PyGridLoadBalancer',
            vpc=vpc,
            internet_facing=True,
            cross_zone_enabled=True
        )

        master_node_url = lb.load_balancer_dns_name + ':5001'

        self.service = ecs_patterns.NetworkLoadBalancedFargateService(
            self,
            'MasterNodeService',

            # Resources
            cluster=cluster,
            cpu=512,
            memory_limit_mib=2048,
            desired_count=1,

            # Load balancer config
            public_load_balancer=True,
            listener_port=5001,

            # Task image options
            task_image_options=ecs_patterns.NetworkLoadBalancedTaskImageOptions(
                container_name='artificien_master_node',
                container_port=5001,
                image=ecs.ContainerImage.from_asset('./pygrid_orchestration'),
                environment={
                    'MASTER_NODE_URL': lb.load_balancer_dns_name + ':5001'
                },
                enable_logging=True,
                log_driver=ecs.AwsLogDriver(
                    stream_prefix='MasterNode',
                    log_group=logs.LogGroup(
                        self, 'MasterNodeLogGroup',
                        removal_policy=cdk.RemovalPolicy.DESTROY,
                        retention=logs.RetentionDays.ONE_MONTH
                    )
                )
            ),
            load_balancer=lb
        )

        # Provide the task the ability to launch new resources
        self.service.service.task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('AWSCloudFormationFullAccess')
        )
        # Provide the task the ability to launch new resources
        self.service.service.task_definition.task_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess')
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
        cdk.CfnOutput(self, 'MasterNodeLoadBalancerDNS', value=master_node_url)
