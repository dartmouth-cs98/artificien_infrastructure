from aws_cdk import (
    core as cdk,
    aws_ec2 as ec2,
    aws_ecs as ecs,
)


class EcsClusterStack(cdk.Stack):
    """
    Simply creates an ECS cluster. This ECS cluster will be the 'home' of all pygrid node deployments.
    By having only one ECS cluster and associated VPC deployment where all ECS service deployments 'live', we avoid
    spinning up unnecessary VPCs and ECS clusters, and save on cost.
    """

    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        self.vpc = ec2.Vpc(self, "PygridVPC", max_azs=2)
        self.cluster = ecs.Cluster(self, 'PyGridCluster', vpc=self.vpc)
