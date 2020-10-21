from aws_cdk import (
    core as cdk,
    aws_iam as iam,
    aws_codebuild as codebuild,
    aws_amplify as amplify
)


class AmplifyStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, **kwargs) -> None:
        """ Deploy the DynamoDB Database and Sample Table """
        super().__init__(scope, id, **kwargs)

        # Create a role, which the website will take on when contact any other services
        amplify_role = iam.Role(self, 'artificienAmplifyRole',
                                assumed_by=iam.ServicePrincipal('amplify.amazonaws.com'),
                                description='A role that provides the amplify website access to DB + other resources')
        amplify_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name('AdministratorAccess'))

        self.amplify_app = amplify.App(
            self,
            'sample-react-app',
            role=amplify_role,
            source_code_provider=amplify.GitHubSourceCodeProvider(
                owner='kenneym',
                repository='amplify-sample-app',
                oauth_token=cdk.SecretValue.plain_text('084f381f25c76d5b417ccfae922a36215bc87950')
            ),
            # build_spec=codebuild.BuildSpec.from_object({  # Alternatively add a `amplify.yml` to the repo
            #     "version": "1.0",
            #     "frontend": {
            #         "phases": {
            #             "pre_build": {
            #                 "commands": ["yarn"]
            #             },
            #             "build": {
            #                 "commands": ["yarn && yarn build"]
            #             }
            #         },
            #         "artifacts": {
            #             "base_directory": "/",
            #             "files": "**/*"
            #         },
            #         "cache": {
            #             "paths": "node_modules/**/*"
            #         }
            #     }})
        )
        master_branch = self.amplify_app.add_branch('main')
