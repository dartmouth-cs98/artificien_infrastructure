# artificien_infrastructure

## Getting Set Up:
- Install aws cli: ` python -m pip install awscli`
- Configure aws credentials for your terminal: `aws configure`, and paste in the access Access Key ID and Secret Access Key for our AWS account.
- Install aws cdk: `npm i -g aws-cdk`

## Deploy the Database:
- Enter top-level directory
- Activate the virtual env `source .env/bin/activate`
- Install python libraries (should be already installed by default, but if you add any new libraries you'll have to rerun this command): `python -m pip install -r requirements.txt`
- Deploy
  - `cdk synth` - to create cloudformation templates
  - `cdk deploy` - to deploy the DynamoDB Sample Table
- Test
  - `pytest tests/unit` to run the unit tests (pre-deployment)
  - `pytest tests/integration` to populate the sample DynamoDB table with data and test that it's queryable (run this AFTER `cdk deploy`)
  
## Query the Database from the outside:
- Use the credentials for the created IAM User `db_user` in order to authenticate calls to the sample Dynamo table