# Artificien: Infrastructure
This repo stores infrastructure and deployment code for the Artificien platform as a single source for deployment. Infrastructure includes a DynamoDB (NoSQL database) utilized by the Marketplace, the severless backend, mechanisms to distribute and train models remotely, and any other cloud resources which may be relevant to the product.

## Architecture
TODO:  overall descriptions of code organization and tools and libraries used

## Setup
- Install aws cli: ` python -m pip install awscli`
- Configure aws credentials for your terminal: `aws configure`, and paste in the access Access Key ID and Secret Access Key for our AWS account.
- Install aws cdk: `npm i -g aws-cdk`

## Deployment

TODO: how to deploy the project

- Enter top-level directory
- Install python libraries: `pip install -r requirements.txt`
- To deploy all resources
  - `cdk synth` - to create cloudformation templates
  - `cdk diff` - to see what changes will be made to our deployments
  - `cdk deploy` - to deploy the DynamoDB Sample Table
- To deploy just one resource:
  - `cdk deploy dynamo-db` or `cdk deploy amplify` or `cdk deploy jupyter` or `cdk deploy cognito`
- Test
  - `pytest tests/unit` to run the unit tests (pre-deployment)
  - `pytest tests/integration` to populate the sample DynamoDB table with data and test that it's queryable (run this AFTER `cdk deploy`)
  
## Usage
- See all aws resources that have been created by viewing the `app.py` file.
- Add new python package requirements by adding them to the `requirements.txt`
- To query the Database from the outside: Use the credentials for the created IAM User `db_user` in order to authenticate calls to the sample Dynamo table

## Authors
* Matt Kenney
* Alex Quill
* Jake Epstein

## Acknowledgments
