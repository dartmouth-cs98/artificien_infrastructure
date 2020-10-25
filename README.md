# Artificien: Infrastructure

This repo stores infrastructure and deployment code for the Artificien platform as a single source for deployment. Infrastructure includes a DynamoDB (NoSQL database) utilized by the Marketplace, the severless backend, mechanisms to distribute and train models remotely, and any other cloud resources which may be relevant to the product.

TODO: super short project description, some sample screenshots or mockups that you keep up-to-date.

## Architecture

TODO:  overall descriptions of code organization and tools and libraries used

## Setup

TODO: how to get the project dev environment up and running, npm install etc, all necessary commands needed, environment variables etc

- Install aws cli: ` python -m pip install awscli`
- Configure aws credentials for your terminal: `aws configure`, and paste in the access Access Key ID and Secret Access Key for our AWS account.
- Install aws cdk: `npm i -g aws-cdk`

## Deployment

TODO: how to deploy the project

- Enter top-level directory
- Activate the virtual env `source .env/bin/activate`
- Install python libraries (should be already installed by default, but if you add any new libraries you'll have to rerun this command): `python -m pip install -r requirements.txt`
- Deploy
  - `cdk synth` - to create cloudformation templates
  - `cdk deploy` - to deploy the DynamoDB Sample Table
- Test
  - `pytest tests/unit` to run the unit tests (pre-deployment)
  - `pytest tests/integration` to populate the sample DynamoDB table with data and test that it's queryable (run this AFTER `cdk deploy`)
  
## Usage
 
To query the Database from the outside:
- Use the credentials for the created IAM User `db_user` in order to authenticate calls to the sample Dynamo table

## Authors

* Matt Kenney '21

## Acknowledgments
