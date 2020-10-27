from aws_cdk import (
    core as cdk,
)
import aws_cdk.aws_iam as iam
from aws_cdk.aws_cognito import (
    UserPool,
    UserPoolClient,
    UserPoolDomain,
    OAuthSettings,
    CognitoDomainOptions,
    CfnIdentityPool,
    CfnIdentityPoolRoleAttachment,
    UserVerificationConfig,
    SignInAliases,
    StandardAttributes,
    StandardAttribute,
    PasswordPolicy,
    AccountRecovery,
    AutoVerifiedAttrs
)


class CognitoStack(cdk.Stack):

    def __init__(self, scope: cdk.Construct, id: str, jupyter_domains: dict, **kwargs) -> None:
        """ Deploy the DynamoDB Database and Sample Table """
        super().__init__(scope, id, **kwargs)

        # Create a user pool - this describes the login requirements and process
        self.user_pool = UserPool(
            self,
            'UserPool',
            user_pool_name='artificienUserPool',
            sign_in_aliases=SignInAliases(username=True, email=True),
            auto_verify=AutoVerifiedAttrs(
                email=True
            ),
            self_sign_up_enabled=True,
            user_verification=UserVerificationConfig(
                email_subject='Verify your email to use Artificien Services',
                email_body='Hello {username}, Thanks for signing up to our app! Your verification code is {####}',
            ),
            standard_attributes=StandardAttributes(
                email=StandardAttribute(
                    required=True,
                    mutable=False
                )
            ),
            password_policy=PasswordPolicy(
                min_length=8
            ),
            account_recovery=AccountRecovery.EMAIL_ONLY
        )

        # How we would go about adding a post user sign up action (i.e. add X user to our DB)
        # self.user_pool.add_trigger(
        #     operation='postConfirmation',
        #     fn=lambda_fn
        # )

        # How we would go about adding Google or Facebook Login, when we get there (convert this TypeScript to Python)
        # This example uses Amazon Login, but this can be switched to Google or FB:
        # const provider = new cognito.UserPoolIdentityProviderAmazon(this, 'Amazon', {
        #     clientId: 'amzn-client-id',
        #     clientSecret: 'amzn-client-secret',
        #     userPool: userpool,
        # });

        # Create Native (with a client secret) and Web (without a client secret) app clients for Cognito
        self.user_pool_client_web = UserPoolClient(
            self,
            'UserPoolClientWeb',
            user_pool_client_name='artificienUserPoolWebClient',
            generate_secret=False,
            user_pool=self.user_pool
        )

        self.user_pool_client_native = UserPoolClient(
            self,
            'UserPoolClientNative',
            user_pool_client_name='artificienUserPoolNativeClient',
            generate_secret=True,
            user_pool=self.user_pool
        )

        # Create a client which will be attached to the jupyter deployment to log users in to Jupyter
        # By using the same Cognito User Pool to login to both the website and JupyterHub, we ensure that
        # our users only need to log in once at the website homepage, and are auto-logged-in to JupyterHub
        self.user_pool_client_jupyter = self.user_pool.add_client(
            id='UserPoolClientJupyter',
            user_pool_client_name='artificienUserPoolJupyterClient',
            generate_secret=True,
            o_auth=OAuthSettings(
                callback_urls=[jupyter_domains['callback_url']],
                logout_urls=[jupyter_domains['signout_url']]
            )
        )

        self.user_pool_domain = UserPoolDomain(
            self,
            'artificienCognitoDomain',
            cognito_domain=CognitoDomainOptions(domain_prefix=jupyter_domains['auth_domain_name']),
            user_pool=self.user_pool,
        )

        # Create an identity pool with one Native app client one Web app client, and one client for Jupyter
        self.identity_pool = CfnIdentityPool(
            self,
            "IdentityPool",
            identity_pool_name='artificienIdentityPool',
            allow_unauthenticated_identities=False,
            cognito_identity_providers=[
                CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.user_pool_client_web.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name,
                ),
                CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.user_pool_client_native.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name,
                ),
                CfnIdentityPool.CognitoIdentityProviderProperty(
                    client_id=self.user_pool_client_jupyter.user_pool_client_id,
                    provider_name=self.user_pool.user_pool_provider_name
                )
            ],
        )

        # Create an authenticated role to authenticate through the Native client
        auth_principal = iam.WebIdentityPrincipal('cognito-identity.amazonaws.com').with_conditions({
            "StringEquals": {"cognito-identity.amazonaws.com:aud": self.identity_pool.ref},
            "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "authenticated"}
        })

        # Create an unauthenticated role to authenticate through the Web client
        unauth_principal = iam.WebIdentityPrincipal('cognito-identity.amazonaws.com').with_conditions({
            "StringEquals": {"cognito-identity.amazonaws.com:aud": self.identity_pool.ref},
            "ForAnyValue:StringLike": {"cognito-identity.amazonaws.com:amr": "unauthenticated"}
        })

        auth_role = iam.Role(self, 'CognitoDefaultAuthRole',
                             role_name='CognitoDefaultAuthRole', assumed_by=auth_principal)

        unauth_role = iam.Role(self, 'CognitoDefaultUnauthRole',
                               role_name='CognitoDefaultUnauthRole', assumed_by=unauth_principal)

        auth_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "mobileanalytics:PutEvents",
                    "cognito-sync:*",
                    "cognito-identity:*"
                ],
                resources=['*']
            )
        )

        unauth_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "mobileanalytics:PutEvents",
                    "cognito-sync:*"
                ],
                resources=['*']
            )
        )

        # Add roles to the user pool
        CfnIdentityPoolRoleAttachment(
            self,
            'IdentityPoolRoleAttachment',
            identity_pool_id=self.identity_pool.ref,
            roles={
                'authenticated': auth_role.role_arn,
                'unauthenticated': unauth_role.role_arn
            }
        )
