from aws_cdk.aws_lambda_event_sources import(
    DynamoEventSource,
    SqsDlq
)
from aws_cdk import core as cdk
import aws_cdk.aws_lambda as aws_lambda
import aws_cdk.aws_sqs as sqs
import aws_cdk.aws_iam as iam
import aws_cdk.aws_s3 as s3


class DataUploadLambda(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, dataset_table, **kwargs) -> None:
        """ Deploy the DynamoDB Database and Data Tables """
        super().__init__(scope, id, **kwargs)

        # Create S3 Bucket to store the sample data CSVs in
        bucket_name = 'artificien-fake-dataset-storage'
        self.bucket = s3.Bucket(self, 'FakeDataBucket', bucket_name=bucket_name)

        # Create the lambda function
        lambda_dir = './lambdas/data_upload_lambda'
        self.lambda_function = aws_lambda.Function(
            self,
            'FakeDataLambda',
            function_name='FakeDataLambda',
            runtime=aws_lambda.Runtime.PYTHON_3_8,
            role=self.create_lambda_role(),
            environment={
                'DYNAMO_TABLE': dataset_table.table_name,  # tells function which table to read from
                'S3_BUCKET': bucket_name  # tells the function which bucket to write to
            },
            code=aws_lambda.Code.from_asset(lambda_dir),  # directory where code is located
            handler='lambda_function.lambda_handler',  # the function the lambda invokes,
            memory_size=128,  # MB - shouldn't need many MB to generate fake data,
            timeout=cdk.Duration.seconds(5)
        )

        # Save failed writes of Fake Datasets to an SQS queue so that we do not experience data loss
        dead_letter_queue = sqs.Queue(self, 'deadLetterQueueNewDataset');

        # Configure the Dynamo Trigger - sends the lambda the new data schema every time a new developer signs on
        self.lambda_function.add_event_source(
            DynamoEventSource(
                table=dataset_table,
                starting_position=aws_lambda.StartingPosition.LATEST,
                batch_size=1,
                retry_attempts=5,
                on_failure=SqsDlq(dead_letter_queue)
            )
        )

    def create_lambda_role(self):
        return iam.Role(
            self,
            "FakeDataLambdaRole",
            role_name="FakeDataLambdaRole",
            assumed_by=iam.ServicePrincipal('lambda.amazonaws.com'),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name('service-role/AWSLambdaBasicExecutionRole'),
                iam.ManagedPolicy.from_aws_managed_policy_name('CloudWatchFullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonS3FullAccess'),
                iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess')
            ]
        )
