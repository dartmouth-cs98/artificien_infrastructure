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

        # Create Sample Table
        self.sample_table_name = 'hello_world_table'
        self.sample_table = Table(
            self, 'HelloWorldDynamoDBTable',
            table_name=self.sample_table_name,
            partition_key=Attribute(
                name='user_id',
                type=AttributeType.STRING
            ),
            billing_mode=BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY  # Change this policy for deployment to production to RETAIN
            # to prevent accidental deletes
        )

        # Grant Full Access to the Principal AWS Account User:
        self.sample_table.grant_full_access(
            iam.AccountRootPrincipal()
        )

        # db_role = iam.Role(self, 'artificienDbRole',
        #                    assumed_by=iam.ServicePrincipal('amplify.amazonaws.com'),
        #                    description='A role that allows the amplify website to access Dynamo')

        # Create a db user, which will be used for read and write ops only (no Admin permissions)
        db_user = iam.User(self, 'artificienDbUser', user_name='db_user')
        access_key = iam.CfnAccessKey(self, 'AccessKey', user_name=db_user.user_name)
        self.sample_table.grant_read_write_data(
            db_user
        )



        # Output db user credentials
        cdk.CfnOutput(self, 'accessKeyId', value=access_key.ref)
        cdk.CfnOutput(self, 'secretAccessKey', value=access_key.attr_secret_access_key)

