from aws_cdk import (
    core as cdk,
    aws_iam as iam
)
from aws_cdk.aws_dynamodb import (
    Table,
    Attribute,
    AttributeType,
    BillingMode
)


class DynamoDBStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        """ Deploy the DynamoDB Database and Sample Table """
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
            removal_policy=core.RemovalPolicy.DESTROY  
        )

        self.app_table = Table(
            self, 'AppTable',
            table_name=self.app_table_name,
            partition_key=Attribute(
                name='app_id',
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY  
        )

        self.model_table = Table(
            self, 'ModelTable',
            table_name=self.model_table_name,
            partition_key=Attribute(
                name='model_id',
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY  
        )

        self.dataset_table = Table(
            self, 'DatasetTable',
            table_name=self.dataset_table_name,
            partition_key=Attribute(
                name='dataset_id',
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=core.RemovalPolicy.DESTROY  
        )


        # Grant Full Access to the Principal AWS Account User:
        self.enterprise_table.grant_full_access(
            iam.AccountRootPrincipal()
        )
        self.user_table.grant_full_access(
            iam.AccountRootPrincipal()
        )
        self.app_table.grant_full_access(
            iam.AccountRootPrincipal()
        )
        self.dataset_table.grant_full_access(
            iam.AccountRootPrincipal()
        )
        self.model_table.grant_full_access(
            iam.AccountRootPrincipal()
        )

        # db_role = iam.Role(self, 'artificienDbRole',
        #                    assumed_by=iam.ServicePrincipal('amplify.amazonaws.com'),
        #                    description='A role that allows the amplify website to access Dynamo')

        # Create a db user, which will be used for read and write ops only (no Admin permissions)
        db_user = iam.User(self, 'artificienDbUser', user_name='db_user')
        access_key = iam.CfnAccessKey(self, 'AccessKey', user_name=db_user.user_name)
        
        self.enterprise_table.grant_read_write_data(
            db_user
        )
        self.user_table.grant_read_write_data(
            db_user
        )
        self.app_table.grant_read_write_data(
            db_user
        )
        self.model_table.grant_read_write_data(
            db_user
        )
        self.dataset_table.grant_read_write_data(
            db_user
        )



        # Output db user credentials
        cdk.CfnOutput(self, 'accessKeyId', value=access_key.ref)
        cdk.CfnOutput(self, 'secretAccessKey', value=access_key.attr_secret_access_key)

