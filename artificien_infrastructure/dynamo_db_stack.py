from aws_cdk import (
    core as cdk,
    aws_iam as iam
)
from aws_cdk.aws_dynamodb import (
    Table,
    Attribute,
    AttributeType,
    BillingMode,
    GlobalSecondaryIndexProps
)


class DynamoDBStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        """ Deploy the DynamoDB Database and Data Tables """
        super().__init__(scope, id, **kwargs)

        # Table Names
        self.enterprise_table_name = 'enterprise_table'
        self.user_table_name = 'user_table'
        self.app_table_name = 'app_table'
        self.model_table_name = 'model_table'
        self.dataset_table_name = 'dataset_table'

        # Create Tables
        self.enterprise_table = Table(
            self, 'EnterpriseTable',
            table_name=self.enterprise_table_name,
            partition_key=Attribute(
                name='enterprise_id',
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY  # Change this policy for deployment to production to RETAIN
            # to prevent accidental deletes
        )

        self.user_table = Table(
            self, 'UserTable',
            table_name=self.user_table_name,
            partition_key=Attribute(
                name='user_id',
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        self.app_table = Table(
            self, 'AppTable',
            table_name=self.app_table_name,
            partition_key=Attribute(
                name='app_id',
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        self.model_table = Table(
            self, 'ModelTable',
            table_name=self.model_table_name,
            partition_key=Attribute(
                name='model_id',
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        self.dataset_table = Table(
            self, 'DatasetTable',
            table_name=self.dataset_table_name,
            partition_key=Attribute(
                name='dataset_id',
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # Add Global Secondary Indices for Select Tables
        self.dataset_table.add_global_secondary_index(
            partition_key=Attribute(
                name='category',
                type=AttributeType.STRING
            ),
            sort_key=Attribute(
                name='num_devices',
                type=AttributeType.NUMBER
            ),
            index_name='category-num_devices-index'
        )

        self.model_table.add_global_secondary_index(
            partition_key=Attribute(
                name='owner_name',
                type=AttributeType.STRING
            ),
            sort_key=Attribute(
                name='active_status',
                type=AttributeType.NUMBER
            ),
            index_name='owner_name-active_status-index'
        )

        # Create a db user, which will be used to access dynamodb
        db_user = iam.User(self, 'artificienDbUser', user_name='db_user')
        db_user.add_managed_policy(
            policy=iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess')
        )

        # Output db user credentials
        access_key = iam.CfnAccessKey(self, 'AccessKey', user_name=db_user.user_name)
        cdk.CfnOutput(self, 'accessKeyId', value=access_key.ref)
        cdk.CfnOutput(self, 'secretAccessKey', value=access_key.attr_secret_access_key)
