import boto3
from boto3.dynamodb.conditions import Key
from flask import Flask, jsonify, request
from pygrid_node_stack import PygridNodeStack
from aws_cdk import core

app = Flask(__name__)
region_name = "us-east-1"

try:
  ecs_client = boto3.client('ecs')

except BaseException as exe:
    print(exe)

#check api status, ping to test
@app.route("/")
def status():
    return "Running"

#retrieve the node endpoint of a given app developer
@app.route("/apps/<string:app_id>")
def get_endpoint(app_id):


#spin up a new node for an app developer
@app.route("/apps", methods=["POST"])
def create_node():
    #pull up dynamo, query
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table('model_table')
    app_id = request.json.get('app_id')
    try:
        response = table.query(
            KeyConditionExpression=Key('app_id').eq(app_id)
        )
    except:
        return jsonify({'error': 'failed to query dynamodb'}), 400

    if response['Items'] is None:
        return jsonify({'error': 'app id not found'}), 400

    try:
        response2 = table.query(
            KeyConditionExpression=Key('node').eq(app_id)
        )
    except:
        return jsonify({'error': 'failed to query dynamodb'}), 400

    if response['response2']:
        return jsonify({'error': 'App already has running node'}), 400

    app = core.App()
    PygridNodeStack(app, app_id, env=core.Environment(region="us-east-1"))














