from aws_cdk import (
    core as cdk,
    aws_iam as iam,
    aws_amplify as amplify
)


class AmplifyStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        """ Deploy the DynamoDB Database and Sample Table """
        super().__init__(scope, id, **kwargs)

        # Create a role, which the website will take on when contact any other services
        self.amplify_role = iam.Role(self, 'amplifyRole',
                                     assumed_by=iam.ServicePrincipal('amplify.amazonaws.com'),
                                     description='A role that provides the amplify website access to DB + other '
                                                 'resources')
        self.amplify_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AdministratorAccess'))
        self.amplify_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess'))

        # Link up our amplify app to our source code
        self.amplify_app = amplify.App(
            self,
            'app',
            role=self.amplify_role,
            source_code_provider=amplify.GitHubSourceCodeProvider(
                owner='dartmouth-cs98',
                repository='artificien_marketplace',
                oauth_token=cdk.SecretValue.plain_text('084f381f25c76d5b417ccfae922a36215bc87950')
            )
        )

        # Add continuous deploys - new deployments on each push to these branches
        master_branch = self.amplify_app.add_branch('amplify-cognito')  # testing environment
        master_branch.add_environment('STAGE', 'testing')

        master_branch = self.amplify_app.add_branch('master')  # dev environment
        master_branch.add_environment('STAGE', 'dev')
